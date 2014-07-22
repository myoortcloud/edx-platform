"""
Group Configuration Tests.
"""
import json
from unittest import skipUnless
from django.conf import settings
from contentstore.utils import reverse_course_url
from contentstore.views.course import GroupConfiguration
from contentstore.tests.utils import CourseTestCase
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.modulestore.tests.factories import ItemFactory


GROUP_CONFIGURATION_JSON = {
    u'name': u'Test name',
    u'description': u'Test description',
}


# pylint: disable=no-member
class GroupConfigurationsBaseTestCase(object):
    """
    Mixin with base test cases for the group configurations.
    """
    def _remove_ids(self, content):
        """
        Remove ids from the response. We cannot predict IDs, because they're
        generated randomly.
        We use this method to clean up response when creating new group configurations.
        Returns a tuple that contains removed group configuration ID and group IDs.
        """
        configuration_id = content.pop("id")
        group_ids = [group.pop("id") for group in content["groups"]]

        return (configuration_id, group_ids)

    def test_required_fields_are_absent(self):
        """
        Test required fields are absent.
        """
        bad_jsons = [
            # must have name of the configuration
            {
                u'description': 'Test description',
                u'groups': [
                    {u'name': u'Group A'},
                    {u'name': u'Group B'},
                ],
            },
            # must have at least two groups
            {
                u'name': u'Test name',
                u'description': u'Test description',
                u'groups': [
                    {u'name': u'Group A'},
                ],
            },
            # an empty json
            {},
        ]

        for bad_json in bad_jsons:
            response = self.client.post(
                self._url(),
                data=json.dumps(bad_json),
                content_type="application/json",
                HTTP_ACCEPT="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("Location", response)
            content = json.loads(response.content)
            self.assertIn("error", content)

    def test_invalid_json(self):
        """
        Test invalid json handling.
        """
        # No property name.
        invalid_json = "{u'name': 'Test Name', []}"

        response = self.client.post(
            self._url(),
            data=invalid_json,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)


# pylint: disable=no-member
@skipUnless(settings.FEATURES.get('ENABLE_GROUP_CONFIGURATIONS'), 'Tests Group Configurations feature')
class GroupConfigurationsListHandlerTestCase(CourseTestCase, GroupConfigurationsBaseTestCase):
    """
    Test cases for group_configurations_list_handler.
    """

    def setUp(self):
        """
        Set up GroupConfigurationsListHandlerTestCase.
        """
        super(GroupConfigurationsListHandlerTestCase, self).setUp()

    def _url(self):
        """
        Return url for the handler.
        """
        return reverse_course_url('group_configurations_list_handler', self.course.id)

    def test_can_retrieve_html(self):
        """
        Check that the group configuration index page responds correctly.
        """
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertIn('New Group Configuration', response.content)

    def test_unsupported_http_accept_header(self):
        """
        Test if not allowed header present in request.
        """
        response = self.client.get(
            self._url(),
            HTTP_ACCEPT="text/plain",
        )
        self.assertEqual(response.status_code, 406)

    def test_can_create_group_configuration(self):
        """
        Test that you can create a group configuration.
        """
        expected = {
            u'description': u'Test description',
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'name': u'Group A', u'version': 1},
                {u'name': u'Group B', u'version': 1},
            ],
        }
        response = self.client.post(
            self._url(),
            data=json.dumps(GROUP_CONFIGURATION_JSON),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        content = json.loads(response.content)
        configuration_id, group_ids = self._remove_ids(content)  # pylint: disable=unused-variable
        self.assertEqual(content, expected)
        # IDs are unique
        self.assertEqual(len(group_ids), len(set(group_ids)))
        self.assertEqual(len(group_ids), 2)
        self.reload_course()
        # Verify that user_partitions in the course contains the new group configuration.
        self.assertEqual(len(self.course.user_partitions), 1)
        self.assertEqual(self.course.user_partitions[0].name, u'Test name')


# pylint: disable=no-member
@skipUnless(settings.FEATURES.get('ENABLE_GROUP_CONFIGURATIONS'), 'Tests Group Configurations feature')
class GroupConfigurationsDetailHandlerTestCase(CourseTestCase, GroupConfigurationsBaseTestCase):
    """
    Test cases for group_configurations_detail_handler.
    """

    ID = 000000000000

    def setUp(self):
        """
        Set up GroupConfigurationsDetailHandlerTestCase.
        """
        super(GroupConfigurationsDetailHandlerTestCase, self).setUp()

    def _url(self, cid=None):
        """
        Return url for the handler.
        """
        cid = cid if cid is not None else self.ID
        return reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': cid},
        )

    def test_can_create_new_group_configuration_if_it_is_not_exist(self):
        """
        PUT new group configuration when no configurations exist in the course.
        """
        expected = {
            u'id': 999,
            u'name': u'Test name',
            u'description': u'Test description',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1},
            ],
        }

        response = self.client.put(
            self._url(cid=999),
            data=json.dumps(GROUP_CONFIGURATION_JSON),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content, expected)
        self.reload_course()
        # Verify that user_partitions in the course contains the new group configuration.
        self.assertEqual(len(self.course.user_partitions), 1)
        self.assertEqual(self.course.user_partitions[0].name, u'Test name')

    def test_can_edit_group_configuration(self):
        """
        Edit group configuration and check its id and modified fields.
        """
        self.course.user_partitions = [
            UserPartition(self.ID, 'First name', 'First description', [Group(0, 'Group A'), Group(1, 'Group B'), Group(2, 'Group C')]),
        ]
        self.save_course()

        expected = {
            u'id': self.ID,
            u'name': u'New Test name',
            u'description': u'New Test description',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1},
            ],
        }
        response = self.client.put(
            self._url(),
            data=json.dumps(expected),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content, expected)
        self.reload_course()
        # Verify that user_partitions is properly updated in the course.
        self.assertEqual(len(self.course.user_partitions), 1)
        self.assertEqual(self.course.user_partitions[0].name, u'New Test name')


class GroupConfigurationsUsageInfoTestCase(CourseTestCase):
    def setUp(self):
        """
        Set up group configurations and split test module.
        """
        super(GroupConfigurationsUsageInfoTestCase, self).setUp()

        self.group_configuration_id_1 = 123456789
        self.group_configuration_1 = {
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }

        self.group_configuration_id_2 = 987654321
        self.group_configuration_2 = {
            u'description': u'Test description 2',
            u'id': self.group_configuration_id_2,
            u'name': u'Group configuration name 2',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }
        self.course.user_partitions = [UserPartition.from_json(self.group_configuration_1)]

        self.vertical = ItemFactory.create(
            category='vertical',
            parent_location=self.course.location,
            display_name='Test Unit 1'
        )
        self.split_test = ItemFactory.create(
            category='split_test',
            parent_location=self.vertical.location,
            user_partition_id=str(self.group_configuration_id_1),
            display_name='Test Content Experiment 1'
        )
        self.save_course()

    def test_group_configuration_used(self):
        """
        Test that right datastructure will be created when group configuration is used.
        """
        expected_usage_info = {
            self.group_configuration_id_1: [
                {
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                    'label': 'Test Unit 1 / Test Content Experiment 1'
                }
            ]
        }
        usage_info = GroupConfiguration._get_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        self.assertEqual(expected_usage_info, usage_info)

    def test_group_configuration_not_used(self):
        """
        Test that right datastructure will be created if group configuration is not used.
        """
        self.store.delete_item(self.split_test.location)
        expected_empty_dict = {}
        result = GroupConfiguration._get_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        self.assertEqual(expected_empty_dict, result)

    def test_usage_info_added(self):
        """
        Test if group configurations json updated successfully.
        """
        updated_configuration = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [{
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ],
            u'usage': [{
                'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                'label': 'Test Unit 1 / Test Content Experiment 1'
            }]
        }]
        self.assertEqual(expected, updated_configuration)

    def test_usage_info_no_experiment(self):
        """
        Test if group configurations json updated successfully if it not used in
        experiments.
        """
        self.store.delete_item(self.split_test.location)
        updated_configuration = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [{
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ],
            u'usage': []
        }]
        self.assertEqual(expected, updated_configuration)

    def test_one_configuration_in_multiple_experiments(self):
        """
        Test if multiple experiments are present in usage info when they use same
        group configuration.
        """
        self.vertical_2 = ItemFactory.create(
            category='vertical',
            parent_location=self.course.location,
            display_name='Test Unit 2'
        )
        self.split_test_2 = ItemFactory.create(
            category='split_test',
            parent_location=self.vertical_2.location,
            user_partition_id=str(self.group_configuration_id_1),
            display_name='Test Content Experiment 2'
        )
        self.save_course()

        updated_configuration = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [{
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ],
            u'usage': [
                {
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                    'label': 'Test Unit 1 / Test Content Experiment 1'
                },
                {
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_2',
                    'label': 'Test Unit 2 / Test Content Experiment 2'
                },
            ]
        }]
        self.assertEqual(expected, updated_configuration)

    def test_two_configurations_two_experiments(self):
        """
        Test if multiple experiments are present in usage info when they use same
        group configuration.
        """
        self.course.user_partitions.append(UserPartition.from_json(self.group_configuration_2))
        self.vertical_2 = ItemFactory.create(
            category='vertical',
            parent_location=self.course.location,
            display_name='Test Unit 2'
        )
        self.split_test_2 = ItemFactory.create(
            category='split_test',
            parent_location=self.vertical_2.location,
            user_partition_id=str(self.group_configuration_id_2),
            display_name='Test Content Experiment 2'
        )
        self.save_course()

        updated_configurations = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [
            {
                u'description': u'Test description 1',
                u'id': self.group_configuration_id_1,
                u'name': u'Group configuration name 1',
                u'version': 1,
                u'groups': [
                    {u'id': 0, u'name': u'Group A', u'version': 1},
                    {u'id': 1, u'name': u'Group B', u'version': 1}
                ],
                u'usage': [{
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                    'label': 'Test Unit 1 / Test Content Experiment 1'
                }]
            },
            {
                u'description': u'Test description 2',
                u'id': self.group_configuration_id_2,
                u'name': u'Group configuration name 2',
                u'version': 1,
                u'groups': [
                    {u'id': 0, u'name': u'Group A', u'version': 1},
                    {u'id': 1, u'name': u'Group B', u'version': 1}
                ],
                u'usage': [{
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_2',
                    'label': 'Test Unit 2 / Test Content Experiment 2'
                }]
            }
        ]
        self.assertEqual(expected, updated_configurations)
