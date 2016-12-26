# -*- coding: utf-8 -*-

from collections import namedtuple

from openassessment.assessment.api import peer as peer_api, staff as staff_api
from openassessment.ga_data import OraAggregateData
from openassessment.test_utils import TransactionCacheResetTest
from openassessment.workflow import api as workflow_api
from submissions import api as sub_api


COURSE_ID = "Test_Course"
ITEM_ID = "item_one"

STUDENT_ID_1 = "Student1"
STUDENT_ITEM_1 = dict(
    student_id=STUDENT_ID_1,
    course_id=COURSE_ID,
    item_id=ITEM_ID,
    item_type="openassessment"
)

STUDENT_ID_2 = "Student2"
STUDENT_ITEM_2 = dict(
    student_id=STUDENT_ID_2,
    course_id=COURSE_ID,
    item_id=ITEM_ID,
    item_type="openassessment"
)

SCORER_ID_1 = "Scorer1"
SCORER_ITEM_1 = dict(
    student_id=SCORER_ID_1,
    course_id=COURSE_ID,
    item_id=ITEM_ID,
    item_type="openassessment"
)

SCORER_ID_2 = "Scorer2"
SCORER_ITEM_2 = dict(
    student_id=SCORER_ID_2,
    course_id=COURSE_ID,
    item_id=ITEM_ID,
    item_type="openassessment"
)

ANSWER = {'text': u"THIS IS A TEST ANSWER"}

RUBRIC_DICT = {
    "criteria": [
        {
            "name": "criterion_1",
            "label": "criterion_1",
            "prompt": "Did the writer keep it secret?",
            "options": [
                {"name": "option_1", "points": "0", "explanation": ""},
                {"name": "option_2", "points": "1", "explanation": ""},
            ]
        },
        {
            "name": u"criterion_2",
            "label": u"criterion_2",
            "prompt": "Did the writer keep it safe?",
            "options": [
                {"name": "option_1", "label": "option_1", "points": "0", "explanation": ""},
                {"name": "option_2", "label": "option_2", "points": "1", "explanation": ""},
            ]
        },
    ]
}

ASSESSMENT_DICT_1 = {
    'overall_feedback': u"这是中国",
    'criterion_feedback': {
        "criterion_2": u"𝓨𝓸𝓾 𝓼𝓱𝓸𝓾𝓵𝓭𝓷'𝓽 𝓰𝓲𝓿𝓮 𝓾𝓹!"
    },
    'options_selected': {
        "criterion_1": "option_1",
        "criterion_2": "option_2",
    },
}

ASSESSMENT_DICT_2 = {
    'overall_feedback': u"这是中国",
    'criterion_feedback': {
        "criterion_2": u"𝓨𝓸𝓾 𝓼𝓱𝓸𝓾𝓵𝓭𝓷'𝓽 𝓰𝓲𝓿𝓮 𝓾𝓹!"
    },
    'options_selected': {
        "criterion_1": "option_2",
        "criterion_2": "option_1",
    },
}

ASSESSMENT_DICT_3 = {
    'overall_feedback': u"这是中国",
    'criterion_feedback': {
        "criterion_2": u"𝓨𝓸𝓾 𝓼𝓱𝓸𝓾𝓵𝓭𝓷'𝓽 𝓰𝓲𝓿𝓮 𝓾𝓹!"
    },
    'options_selected': {
        "criterion_1": "option_2",
        "criterion_2": "option_2",
    },
}

MockUser = namedtuple('MockUser', ['username'])


def mock_user_by_anonymous_id(anonymous_id):
    return MockUser(anonymous_id)


class OraAggregateDataTest(TransactionCacheResetTest):

    def _create_submission(self, student_item_dict, staff_assessment=False):
        """
        Creates a submission and initializes a peer grading workflow.
        """
        submission = sub_api.create_submission(student_item_dict, ANSWER)
        submission_uuid = submission['uuid']
        if staff_assessment:
            staff_api.on_init(submission_uuid)
            workflow_api.create_workflow(submission_uuid, ['staff'])
        else:
            peer_api.on_start(submission_uuid)
            workflow_api.create_workflow(submission_uuid, ['peer'])
        return submission

    def _create_assessment(self, submission_uuid, scorer_id, assessment_dict, staff_assessment=False):
        """
        Creates an assessment for the given submission.
        """
        if staff_assessment:
            return staff_api.create_assessment(
                submission_uuid,
                scorer_id,
                assessment_dict['options_selected'],
                assessment_dict['criterion_feedback'],
                assessment_dict['overall_feedback'],
                RUBRIC_DICT
            )
        else:
            return peer_api.create_assessment(
                submission_uuid,
                scorer_id,
                assessment_dict['options_selected'],
                assessment_dict['criterion_feedback'],
                assessment_dict['overall_feedback'],
                RUBRIC_DICT,
                2
            )

    def _assert_peer_row(
        self, row, username, content, status, points_earned, points_possible,
        grade_count, being_graded_count, scored_count, peer_scored_flags, peer_scorer_usernames, peer_rubric_points_list,
        staff_scored_flag, staff_scorer_usernames, staff_rubric_points_list
    ):
        """
        Asserts peer assessment row except datetime column.
        """
        self.assertEqual(row[0], username)
        self.assertEqual(row[1], content)
        self.assertEqual(row[3], status)
        self.assertEqual(row[4], points_earned)
        self.assertEqual(row[5], points_possible)
        self.assertEqual(row[7], grade_count)
        self.assertEqual(row[8], being_graded_count)
        self.assertEqual(row[9], scored_count)
        self.assertEqual(row[10], peer_scored_flags)
        self.assertEqual(row[11], peer_scorer_usernames)
        for i, points in enumerate(peer_rubric_points_list):
            self.assertEqual(row[12 + i], points)

        peer_count = len(peer_rubric_points_list)
        self.assertEqual(row[12 + peer_count], staff_scored_flag)
        self.assertEqual(row[13 + peer_count], staff_scorer_usernames)
        for i, points in enumerate(staff_rubric_points_list):
            self.assertEqual(row[14 + peer_count + i], points)

    def _assert_staff_row(
        self, row, username, content, status, points_earned, points_possible,
        staff_scored_flag, staff_scorer_usernames, staff_rubric_points_list
    ):
        """
        Asserts staff assessment row except datetime column.
        """
        self.assertEqual(row[0], username)
        self.assertEqual(row[1], content)
        self.assertEqual(row[3], status)
        self.assertEqual(row[4], points_earned)
        self.assertEqual(row[5], points_possible)
        self.assertEqual(row[7], staff_scored_flag)
        self.assertEqual(row[8], staff_scorer_usernames)
        for i, points in enumerate(staff_rubric_points_list):
            self.assertEqual(row[9 + i], points)

    def test_collect_ora2_data_no_submissions(self):
        submissions, header, rows = OraAggregateData.collect_ora2_data(COURSE_ID, ITEM_ID, mock_user_by_anonymous_id)

        self.assertEqual(submissions, [])
        self.assertEqual(header, [])
        self.assertEqual(rows, [])

    def test_collect_ora2_data_peer(self):
        # Create submission
        submission_1 = self._create_submission(STUDENT_ITEM_1)
        scorer_submission_1 = self._create_submission(SCORER_ITEM_1)
        scorer_submission_2 = self._create_submission(SCORER_ITEM_2)

        # Create Peer assessment by Scorer1
        peer_api.get_submission_to_assess(scorer_submission_1['uuid'], 2)
        self._create_assessment(scorer_submission_1['uuid'], SCORER_ID_1, ASSESSMENT_DICT_1)
        peer_api.get_submission_to_assess(scorer_submission_1['uuid'], 2)
        self._create_assessment(scorer_submission_1['uuid'], SCORER_ID_1, ASSESSMENT_DICT_1)

        # Create Peer assessment by Scorer2
        peer_api.get_submission_to_assess(scorer_submission_2['uuid'], 2)
        self._create_assessment(scorer_submission_2['uuid'], SCORER_ID_2, ASSESSMENT_DICT_2)
        peer_api.get_submission_to_assess(scorer_submission_2['uuid'], 2)
        self._create_assessment(scorer_submission_2['uuid'], SCORER_ID_2, ASSESSMENT_DICT_2)

        # Create Staff assessment for Scorer2
        self._create_assessment(scorer_submission_2['uuid'], SCORER_ID_1, ASSESSMENT_DICT_2, True)

        # Update workflow
        workflow_api.get_workflow_for_submission(submission_1['uuid'], {'peer': {'must_be_graded_by': 2, 'must_grade': 0}})
        workflow_api.get_workflow_for_submission(scorer_submission_1['uuid'], {'peer': {'must_be_graded_by': 2, 'must_grade': 0}})
        workflow_api.get_workflow_for_submission(scorer_submission_2['uuid'], {'peer': {'must_be_graded_by': 2, 'must_grade': 0}})

        # Create submission (not being graded)
        submission_2 = self._create_submission(STUDENT_ITEM_2)

        submissions, header, rows = OraAggregateData.collect_ora2_data(COURSE_ID, ITEM_ID, mock_user_by_anonymous_id)

        self.assertItemsEqual(
            [sub['uuid'] for sub in submissions],
            [submission_1['uuid'], scorer_submission_1['uuid'], scorer_submission_2['uuid'], submission_2['uuid']]
        )

        self.assertItemsEqual(header, [
            'Username',
            'Submission Content',
            'Submission Created At',
            'Status',
            'Points Earned',
            'Points Possible',
            'Score Created At',
            'Grade Count',
            'Being Graded Count',
            'Scored Count',
            'Peer Scored Flags',
            'Peer Scorer Usernames',
            'Peer Rubric(criterion_1) Points',
            'Peer Rubric(criterion_2) Points',
            'Staff Scored Flag',
            'Staff Scorer Usernames',
            'Staff Rubric(criterion_1) Points',
            'Staff Rubric(criterion_2) Points',
        ])

        self.assertEquals(4, len(rows))

        self._assert_peer_row(
            rows[0], 'Student1', 'THIS IS A TEST ANSWER', 'done', 2, 2,
            0, 2, 2, '1,1', 'Scorer1,Scorer2', ['0,1', '1,0'], 0, '', ['', '']
        )
        self._assert_peer_row(
            rows[1], 'Scorer1', 'THIS IS A TEST ANSWER', 'waiting', '', '',
            2, 1, 0, '0', 'Scorer2', ['1', '0'], 0, '', ['', '']
        )
        self._assert_peer_row(
            rows[2], 'Scorer2', 'THIS IS A TEST ANSWER', 'done', 1, 2,
            2, 1, 0, '0', 'Scorer1', ['0', '1'], 1, 'Scorer1', ['1', '0']
        )
        self._assert_peer_row(
            rows[3], 'Student2', 'THIS IS A TEST ANSWER', 'peer', '', '',
            0, 0, 0, '', '', ['', ''], 0, '', ['', '']
        )

    def test_collect_ora2_data_peer_no_assessments(self):
        # Create submission
        submission = self._create_submission(STUDENT_ITEM_1)

        submissions, header, rows = OraAggregateData.collect_ora2_data(COURSE_ID, ITEM_ID, mock_user_by_anonymous_id)

        self.assertItemsEqual([sub['uuid'] for sub in submissions], [submission['uuid']])

        self.assertItemsEqual(header, [
            'Username',
            'Submission Content',
            'Submission Created At',
            'Status',
            'Points Earned',
            'Points Possible',
            'Score Created At',
            'Grade Count',
            'Being Graded Count',
            'Scored Count',
            'Peer Scored Flags',
            'Peer Scorer Usernames',
            'Staff Scored Flag',
            'Staff Scorer Usernames',
        ])

        self._assert_peer_row(
            rows[0], 'Student1', 'THIS IS A TEST ANSWER', 'peer', '', '', 0, 0, 0, '', '', [], 0, '', []
        )

    def test_collect_ora2_data_staff(self):
        # Create submission
        submission = self._create_submission(STUDENT_ITEM_1, True)
        scorer_submission_1 = self._create_submission(SCORER_ITEM_1, True)
        scorer_submission_2 = self._create_submission(SCORER_ITEM_2, True)

        # Create Staff assessment
        self._create_assessment(submission['uuid'], SCORER_ID_2, ASSESSMENT_DICT_1, True)
        self._create_assessment(scorer_submission_1['uuid'], SCORER_ID_2, ASSESSMENT_DICT_2, True)
        self._create_assessment(scorer_submission_1['uuid'], STUDENT_ID_1, ASSESSMENT_DICT_1, True)
        self._create_assessment(scorer_submission_1['uuid'], SCORER_ID_2, ASSESSMENT_DICT_3, True)

        # Update workflow
        workflow_api.get_workflow_for_submission(submission['uuid'], None)
        workflow_api.get_workflow_for_submission(scorer_submission_1['uuid'], None)
        workflow_api.get_workflow_for_submission(scorer_submission_2['uuid'], None)

        submissions, header, rows = OraAggregateData.collect_ora2_data(COURSE_ID, ITEM_ID, mock_user_by_anonymous_id)

        self.assertItemsEqual(
            [sub['uuid'] for sub in submissions],
            [submission['uuid'], scorer_submission_1['uuid'], scorer_submission_2['uuid']]
        )

        self.assertItemsEqual(header, [
            'Username',
            'Submission Content',
            'Submission Created At',
            'Status',
            'Points Earned',
            'Points Possible',
            'Score Created At',
            'Staff Scored Flag',
            'Staff Scorer Usernames',
            'Staff Rubric(criterion_1) Points',
            'Staff Rubric(criterion_2) Points',
        ])

        self._assert_staff_row(
            rows[0], 'Student1', 'THIS IS A TEST ANSWER', 'done', 1, 2, 1, 'Scorer2', ['0', '1']
        )
        self._assert_staff_row(
            rows[1], 'Scorer1', 'THIS IS A TEST ANSWER', 'done', 2, 2, 1, 'Scorer2,Student1,Scorer2', ['1,0,1', '0,1,1']
        )
        self._assert_staff_row(
            rows[2], 'Scorer2', 'THIS IS A TEST ANSWER', 'waiting', '', '', 0, '', ['', '']
        )

    def test_collect_ora2_data_staff_no_assessments(self):
        # Create submission
        submission = self._create_submission(STUDENT_ITEM_1, True)

        submissions, header, rows = OraAggregateData.collect_ora2_data(COURSE_ID, ITEM_ID, mock_user_by_anonymous_id)

        self.assertItemsEqual([sub['uuid'] for sub in submissions], [submission['uuid']])

        self.assertItemsEqual(header, [
            'Username',
            'Submission Content',
            'Submission Created At',
            'Status',
            'Points Earned',
            'Points Possible',
            'Score Created At',
            'Staff Scored Flag',
            'Staff Scorer Usernames',
        ])

        self._assert_staff_row(rows[0], 'Student1', 'THIS IS A TEST ANSWER', 'waiting', '', '', 0, '', [])
