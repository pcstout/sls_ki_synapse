import pytest
import tempfile
import os
import json
from tests.synapse_test_helper import SynapseTestHelper
from core.synapse import Synapse
from synapseclient import EntityViewSchema, Schema, Column, Table, Row, RowSet
import time
import kirallymanager.manager as krm

# Load Environment variables.
with open('private.test.env.json') as f:
    config = json.load(f).get('test')

    # Validate required properties are present
    for prop in['SYNAPSE_USERNAME', 'SYNAPSE_PASSWORD']:
        if not prop in config or not config[prop]:
            raise Exception(
                'Property: "{0}" is missing in private.test.env.json'.format(prop))

    for key, value in config.items():
        os.environ[key] = value


@pytest.fixture(scope='session')
def syn_client():
    return Synapse.client()


@pytest.fixture()
def syn_test_helper():
    """
    Provides the SynapseTestHelper as a fixture per function.
    """
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


@pytest.fixture(scope='session')
def syn_test_helper_session(request):
    """
    Provides the SynapseTestHelper as a fixture per session.
    """
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


@pytest.fixture
def rally_number():
    return round(time.time())


@pytest.fixture(scope='session')
def rally_number_session():
    return round(time.time())


@pytest.fixture(scope='session')
def rally_setup(syn_client, syn_test_helper_session, temp_file_session):
    master_project = syn_test_helper_session.create_project(
        prefix='Master Project ')

    master_wiki_template = syn_test_helper_session.create_file(
        parent=master_project, path=temp_file_session)
    master_task_wiki_template = syn_test_helper_session.create_file(
        parent=master_project, path=temp_file_session)
    master_rally_wiki_template = syn_test_helper_session.create_file(
        parent=master_project, path=temp_file_session)

    rally_table_schema = syn_client.store(EntityViewSchema(
        name=syn_test_helper_session.uniq_name(prefix='Rally View '),
        parent=master_project,
        scopes=[master_project],
        columns=[Column(name='rally', columnType='INTEGER')])
    )

    task_table_schema = syn_client.store(EntityViewSchema(name=syn_test_helper_session.uniq_name(
        prefix='Task View '), parent=master_project, scopes=[master_project]))

    all_files_schema = syn_client.store(EntityViewSchema(name=syn_test_helper_session.uniq_name(
        prefix='Master All Files View '), parent=master_project, scopes=[master_project]))

    rally_admin_team = syn_test_helper_session.create_team(
        prefix='Rally Admin Team ')

    rally_admin_project = syn_test_helper_session.create_project(
        prefix='Rally Admin Project ',
        rallyAdminTeamId=rally_admin_team.id,
        rallyTableId=rally_table_schema.id,
        wikiMasterTemplateId=master_wiki_template.id,
        taskTableTemplateId=task_table_schema.id
    )

    result = {
        'master_project': master_project,
        'master_wiki_template': master_wiki_template,
        'master_task_wiki_template': master_task_wiki_template,
        'master_rally_wiki_template': master_rally_wiki_template,
        'task_table_schema': task_table_schema,
        'all_files_schema': all_files_schema,
        'rally_admin_team': rally_admin_team,
        'rally_admin_project': rally_admin_project,

        'rally_config': {
            'consortium': 'Test Consortium',
            'rallyAdminProjectId': rally_admin_project.id,
            'wikiTaskTemplateId': master_task_wiki_template.id,
            'wikiRallyTemplateId': master_rally_wiki_template.id,
            'allFilesSchemaId': all_files_schema.id,
            'defaultRallyTeamMembers': [],
            'defaultRallyTeamMembersStr': '',
            'rallyAdminTeamPermissions': ["DOWNLOAD", "CHANGE_PERMISSIONS", "CHANGE_SETTINGS", "MODERATE", "READ", "UPDATE", "DELETE", "CREATE"],
            'rallyAdminTeamPermissionsStr': '"DOWNLOAD", "CHANGE_PERMISSIONS", "CHANGE_SETTINGS", "MODERATE", "READ", "UPDATE", "DELETE", "CREATE"',
            'sprintFolders': ["Data", "Research Questions", "Results", "Sprint kickoff", "Report out", "Timeline"],
            'sprintFoldersStr': '"Data", "Research Questions", "Results", "Sprint kickoff", "Report out", "Timeline"',
            'posts': [{"title": "test", "messageMarkdown": "Use this post for a daily check in."}],
            'postsStr': '{title: "test", messageMarkdown: "Use this post for a daily check in."}',
        }
    }
    return result


@pytest.fixture(scope='session')
def rally_project(syn_test_helper_session, rally_setup, rally_number_session):
    project = krm.createRally(
        Synapse.client(), rally_number_session, rally_setup['rally_config'])
    syn_test_helper_session.dispose_of(project)
    return project


@pytest.fixture
def temp_file(syn_test_helper):
    """
    Generates a temp file containing the SynapseTestHelper.uniq_name per function.
    """
    fd, tmp_filename = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(syn_test_helper.uniq_name())
    yield tmp_filename

    if os.path.isfile(tmp_filename):
        os.remove(tmp_filename)


@pytest.fixture(scope='session')
def temp_file_session(syn_test_helper_session):
    """
    Generates a temp file containing the SynapseTestHelper.uniq_name per session.
    """
    fd, tmp_filename = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(syn_test_helper_session.uniq_name())
    yield tmp_filename

    if os.path.isfile(tmp_filename):
        os.remove(tmp_filename)