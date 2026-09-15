"""Parse the production workflow wiring for isolated legacy and GPID deployment."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def workflow(name: str) -> dict:
    """Read the actual source workflow, e.g. workflow('pages.yml')."""
    return yaml.safe_load((ROOT / '.github/workflows' / name).read_text(encoding='utf-8'))


def test_mutable_dev_build_has_no_publication_job_or_environment():
    value = workflow('pages.yml')
    for job in value['jobs'].values():
        assert 'environment' not in job
        assert job.get('permissions', value['permissions']) == {'contents': 'read'}
        assert not any('create-github-app-token' in step.get('uses', '') for step in job['steps'])
    assert any('actions/upload-artifact@' in step.get('uses', '')
               for step in value['jobs']['deploy-dev-preview']['steps'])


def test_release_and_mutable_dev_execute_on_separate_runners():
    jobs = workflow('release-docs.yml')['jobs']
    assert 'build-dev' in jobs
    stable = str(jobs['build']['steps'])
    assert 'current-dev/scripts/' not in stable
    assert 'ref: dev' not in stable
    for job in jobs.values():
        assert 'environment' not in job
        assert job['permissions'] == {'contents': 'read'}
    steps = workflow('release-pages.yml')['jobs']['deploy']['steps']
    assert any('import-docs release-source release-artifact' in s.get('run', '') for s in steps)
    assert any('import-dev current-dev release-dev-artifact' in s.get('run', '') for s in steps)


def test_legacy_deploys_use_protected_controller_and_final_fresh_authority():
    value = workflow('release-pages.yml')
    assert value['concurrency'] == {'group': 'pages', 'cancel-in-progress': False}
    for job in value['jobs'].values():
        steps = job['steps']
        root_checkouts = [step for step in steps if 'actions/checkout@' in step.get('uses', '')
                          and 'path' not in step.get('with', {})]
        assert len(root_checkouts) == 1
        assert root_checkouts[0]['with']['ref'] == '${{ github.sha }}'
        assert root_checkouts[0]['with']['persist-credentials'] is False
        assert 'legacy-pages.js check' in steps[-2]['run']
        assert 'actions/deploy-pages@' in steps[-1]['uses']
        assert not any('rebuild-docs.js --all' in step.get('run', '') for step in steps)
        assert any('legacy-pages.js archive' in step.get('run', '') for step in steps)


def test_gpid_deployment_rechecks_after_environment_delay_and_artifact_upload():
    value = workflow('release-controller-docs.yml')
    assert 'false &&' in value['jobs']['register']['if']
    assert 'environment' not in value['jobs']['dev-preview']
    assert value['jobs']['deploy']['environment']['name'] == 'github-pages'
    steps = value['jobs']['deploy']['steps']
    assert 'authorize-deploy' in steps[-2]['run']
    assert steps[-2].get('continue-on-error', False) is False
    assert steps[-1].get('if', 'success()') == 'success()'
    commands = [line.strip() for line in steps[-2]['run'].splitlines()
                if line.strip() and not line.lstrip().startswith('#')]
    assert 'authorize-deploy' in commands[-1]
    assert all(any(guard in line for line in commands[:-1]) for guard in
               ['sha256sum composition/.docs-deployment.json', '/branches/dev', '/releases/latest'])
    assert 'actions/deploy-pages@' in steps[-1]['uses']
    upload = next(i for i, step in enumerate(steps) if 'actions/upload-pages-artifact@' in step.get('uses', ''))
    authority = next(i for i, step in enumerate(steps) if step.get('id') == 'authority')
    assert upload < authority < len(steps) - 2
    assert steps[authority]['with']['permission-contents'] == 'read'
    assert 'secrets.RELEASE_PUBLISHING_APP' not in str(steps)
