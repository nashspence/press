"""Publisher consumer contracts against the installed, immutable GuavaJam core."""
from pathlib import Path
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PublisherTests(unittest.TestCase):
    def command(self, repo, *args, ok=True):
        result = subprocess.run(args, cwd=repo, text=True, capture_output=True)
        if ok:
            self.assertEqual(0, result.returncode, result.stderr)
        else:
            self.assertNotEqual(0, result.returncode)
        return result

    def make(self, repo, target, *variables, ok=True):
        return self.command(repo, 'make', '--no-print-directory', '--file', str(ROOT / 'Makefile'),
                            target, 'PYTHON=' + sys.executable, *variables, ok=ok)

    def test_core_is_an_installed_locked_git_dependency_without_the_view(self):
        project = tomllib.loads((ROOT / 'pyproject.toml').read_text())
        source = project['tool']['uv']['sources']['guavajam-core']
        self.assertRegex(source['rev'], r'^[0-9a-f]{40}$')
        self.assertEqual('https://github.com/nashspence/guavajam', source['git'])
        self.assertEqual('projects/core', source['subdirectory'])
        package = importlib.metadata.distribution('guavajam-core')
        direct = json.loads(package.read_text('direct_url.json'))
        self.assertEqual(source['rev'], direct['vcs_info']['commit_id'])
        self.assertEqual('projects/core', direct['subdirectory'])
        self.assertIsNone(importlib.util.find_spec('guavajam'))

    def test_setup_then_help_and_asset_commands_work_in_one_parallel_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            credentials = Path(directory) / 'credentials.example'
            result = self.command(
                ROOT, 'env', 'MISE_LOCKFILE=false', 'make', '--no-print-directory',
                '--file', str(ROOT / 'Makefile'), '--jobs=2', 'setup', 'help',
                'asset-credentials', 'PYTHON=' + sys.executable, 'OUTPUT=' + str(credentials))
            targets = {line.split()[0] for line in result.stdout.splitlines() if line.startswith('  ')}
            self.assertTrue({'asset-credentials', 'image', 'asset-upload', 'asset-pin',
                             'assets-gc', 'asset-retire', 'assets-policy-plan',
                             'assets-policy-apply', 'gateway-plan', 'gateway-deploy'} <= targets)
            self.assertEqual(0o600, credentials.stat().st_mode & 0o777)

    def test_offline_asset_commands_use_the_callers_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.command(repo, 'git', 'init', '-q', '-b', 'main')
            (repo / 'asset-policy.json').write_text(json.dumps({'origin': 'https://assets.example.org'}))
            asset = repo / 'attachment.txt'
            asset.write_bytes(b'Original attachment bytes.\n')
            key = 'sha256/' + hashlib.sha256(asset.read_bytes()).hexdigest() + '.bin'
            prepared = self.make(repo, 'image', 'FILE=' + str(asset))
            self.assertIn('Object: ' + key, prepared.stdout)
            self.assertIn('URL: https://assets.example.org/' + key, prepared.stdout)
            plan = self.make(repo, 'gateway-plan', 'S3_ENV=' + str(repo / 'absent-credentials'))
            self.assertIn('https://assets.example.org', plan.stdout)
            self.assertIn('no API writes or credential reads', plan.stdout)

    def test_real_authoring_signing_and_publication_check_use_installed_core(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repo = parent / 'publications'
            repo.mkdir()
            self.command(repo, 'git', 'init', '-q', '-b', 'main')
            self.command(repo, 'git', 'config', 'user.name', 'Example Publisher')
            self.command(repo, 'git', 'config', 'user.email', 'publisher@example.org')
            self.command(repo, 'git', 'config', 'commit.gpgsign', 'false')
            self.make(repo, 'work', 'WORK=field-notes', 'TITLE=Field Notes', 'AUTHOR=Example Author')
            source = repo / 'works/field-notes/manuscript.md'
            self.assertTrue(source.is_file())
            self.assertIn('author: Example Author', source.read_text())
            self.make(repo, 'work', 'WORK=field-notes', 'TITLE=Overwrite', 'AUTHOR=Example', ok=False)
            self.command(repo, 'git', 'add', '-A')
            self.make(repo, 'check-source')
            self.make(repo, 'check-assets')
            self.command(repo, 'git', 'commit', '-qm', 'Reviewed draft')
            draft = self.command(repo, 'git', 'rev-parse', 'HEAD').stdout.strip()
            self.make(repo, 'publication-prepare', 'REV=' + draft, 'WORK=field-notes', 'PUBLISHED=', ok=False)
            prepared = self.make(repo, 'publication-prepare', 'REV=' + draft, 'WORK=field-notes',
                                 'PUBLISHED=2026-11-13', 'LABEL=Initial edition')
            receipt = json.loads(prepared.stdout)
            self.assertTrue(receipt['assets_verified'])
            self.assertFalse(receipt['retention_verified'])  # This edition has no asset dependencies.
            trailers = receipt['publication_trailers']
            self.assertEqual(['Press-Publication: 1', 'Press-Work: works/field-notes/manuscript.md',
                              'Press-Published: 2026-11-13', 'Press-Label: Initial edition'], trailers)
            key = parent / 'key'
            self.command(repo, 'ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(key))
            self.command(repo, 'git', 'config', 'gpg.format', 'ssh')
            self.command(repo, 'git', 'config', 'user.signingkey', str(key))
            message = '\n'.join(trailers)
            self.command(repo, 'git', 'commit', '--allow-empty', '-S', '-m', 'Publish', '-m', message)
            revision = self.command(repo, 'git', 'rev-parse', 'HEAD').stdout.strip()
            signers = parent / 'allowed-signers'
            signers.write_text('publisher namespaces="git" ' + key.with_suffix('.pub').read_text())
            result = self.make(repo, 'publication-check', 'REV=' + revision, 'SSH_ALLOWED_SIGNERS=' + str(signers))
            self.assertEqual(revision, json.loads(result.stdout)['revision'])
            # A signed content-changing commit must still fail the publication shape contract.
            source.write_text(source.read_text().replace('Field Notes', 'Changed Notes'))
            self.command(repo, 'git', 'commit', '-S', '-am', 'Changed content', '-m', message)
            changed = self.command(repo, 'git', 'rev-parse', 'HEAD').stdout.strip()
            self.make(repo, 'publication-check', 'REV=' + changed, 'SSH_ALLOWED_SIGNERS=' + str(signers), ok=False)

    def test_exported_resources_are_from_the_installed_distribution_and_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credentials = root / 'credentials.example'
            self.make(ROOT, 'asset-credentials', 'OUTPUT=' + str(credentials))
            self.assertEqual(0o600, credentials.stat().st_mode & 0o777)
            from guavajam_core.asset_storage import VARIABLES
            fields = {line.partition('=')[0] for line in credentials.read_text().splitlines()
                      if line and not line.startswith('#')}
            self.assertEqual(VARIABLES, fields)
            self.make(ROOT, 'asset-credentials', 'OUTPUT=' + str(credentials), ok=False)
            capture = root / 'capture'
            self.make(ROOT, 'capture', 'OUTPUT=' + str(capture))
            self.assertTrue((capture / 'manifest.json').is_file())
            self.assertTrue((capture / 'capture.mjs').is_file())
            settings = root / 'press-site.json'
            self.make(ROOT, 'site-template', 'OUTPUT=' + str(settings))
            self.assertEqual('press.site.v1', json.loads(settings.read_text())['schema'])

    def test_independent_signer_policy_and_locked_setup_are_in_every_verification_workflow(self):
        for name in ['validate-source', 'audit-source']:
            workflow = yaml.load((ROOT / '.github/workflows' / (name + '.yml')).read_text(), Loader=yaml.BaseLoader)
            for job in workflow['jobs'].values():
                self.assertTrue(any(step.get('run') == 'make setup' for step in job['steps']))
                check = next(step for step in job['steps'] if 'guavajam_core.check_publications' in step.get('run', ''))
                if '--offline' not in check['run']:
                    self.assertIn('--require-retention', check['run'])
                for key in ['PRESS_PUBLISHER_GPG_FINGERPRINTS', 'PRESS_PUBLISHER_GPG_PUBLIC_KEYS', 'PRESS_PUBLISHER_SSH_SIGNERS']:
                    self.assertEqual('${{ vars.' + key + ' }}', check['env'][key])

    def test_asset_maintenance_keeps_publisher_owned_secret_and_retirement_gates(self):
        workflow = yaml.load((ROOT / '.github/workflows/maintain-assets.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertNotIn('pull_request', workflow['on'])
        self.assertNotIn('pull_request_target', workflow['on'])
        self.assertEqual('false', workflow['concurrency']['cancel-in-progress'])
        job = workflow['jobs']['maintain']
        self.assertIn("github.ref == 'refs/heads/main'", job['if'])
        self.assertIn("vars.PRESS_ASSET_MAINTENANCE_ENABLED == 'true'", job['if'])
        self.assertEqual('press-assets', job['environment'])
        operation = next(step for step in job['steps'] if 'OPERATION' in step.get('env', {}))
        retirement = next(step for step in job['steps'] if 'PRESS_ASSET_RETIRE_TOKEN' in step.get('env', {}))
        self.assertEqual("inputs.operation != 'retire'", operation['if'])
        self.assertEqual("inputs.operation == 'retire'", retirement['if'])
        self.assertNotIn('PRESS_ASSET_RETIRE_TOKEN', operation['env'])
        from guavajam_core.asset_storage import VARIABLES
        self.assertTrue(VARIABLES.isdisjoint(retirement['env']))
        credentials = {'S3_ACCESS_KEY_ID', 'S3_SECRET_ACCESS_KEY', 'S3_SESSION_TOKEN'}
        for name in VARIABLES:
            source = 'secrets' if name in credentials else 'vars'
            self.assertEqual('${{ ' + source + '.' + name + ' }}', operation['env'][name])
        self.assertRegex((ROOT / 'Makefile').read_text(), r'(?m)^REQUIRE_RETENTION \?= 1$')


if __name__ == '__main__':
    unittest.main()
