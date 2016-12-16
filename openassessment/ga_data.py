
from collections import OrderedDict

from openassessment.assessment.api.peer import PEER_TYPE
from openassessment.assessment.api.staff import STAFF_TYPE
from openassessment.assessment.models import Assessment, PeerWorkflow, PeerWorkflowItem
from openassessment.assessment.serializers import RubricSerializer
from openassessment.workflow.models import AssessmentWorkflow
from submissions import api as sub_api


class OraAggregateData(object):

    @classmethod
    def _build_staff_assessment_cell(cls, rubric, assessments, user_by_anonymous_id):

        header = [
            'Staff Scored Flag',
            'Staff Scorer Usernames'
        ]
        row = [
            1 if assessments else 0,
            ','.join([user_by_anonymous_id(assessment.scorer_id).username for assessment in assessments]),
        ]
        # 'Rubric points'
        scores = scores_by_criterion(assessments)
        if 'criteria' in rubric:
            for criterion in rubric['criteria']:
                header.append('Staff Rubric(%s) Points' % criterion['name'])
                row.append(','.join(map(str, scores[criterion['name']])) if criterion['name'] in scores else '')
        return header, row

    @classmethod
    def _build_peer_assessment_cell(cls, submission_uuid, rubric, assessments, user_by_anonymous_id):

        def _get_scored_flag(assessment):
            if assessment.score_type == PEER_TYPE:
                workflow_item = PeerWorkflowItem.objects.filter(assessment=assessment)[0]
                return 1 if workflow_item.scored else 0
            else:
                return 0

        header, row = [], []

        peer_workflow = PeerWorkflow.get_by_submission_uuid(submission_uuid)
        if peer_workflow:
            peer_workflow_items = PeerWorkflowItem.objects.filter(
                author=peer_workflow,
                submission_uuid=submission_uuid,
                assessment__isnull=False
            ).select_related('assessment').order_by('assessment')

            header.extend([
                'Grade Count',
                'Being Graded Count',
                'Scored Count',
                'Peer Scored Flags',
                'Peer Scorer Usernames'
            ])

            row.extend([
                peer_workflow.num_peers_graded() if peer_workflow else 0,
                len(peer_workflow_items) if peer_workflow_items else 0,
                len([item for item in peer_workflow_items if item.scored]) if peer_workflow_items else 0,
                ','.join([str(_get_scored_flag(assessment)) for assessment in assessments]),
                ','.join([user_by_anonymous_id(assessment.scorer_id).username for assessment in assessments]),
            ])

            # 'Rubric points'
            if 'criteria' in rubric:
                scores = scores_by_criterion(assessments)
                for criterion in rubric['criteria']:
                    header.append('Peer Rubric(%s) Points' % criterion['name'])
                    row.append(','.join(map(str, scores[criterion['name']])) if criterion['name'] in scores else '')

        return header, row

    @classmethod
    def collect_ora2_data(cls, course_key, item_location, user_by_anonymous_id):
        header = [
            'Username',
            'Submission Content',
            'Submission Created At',
            'Status',
            'Points Earned',
            'Points Possible',
            'Score Created At',
        ]

        header_extra = []
        rows = []

        submissions = sorted(
            sub_api.get_all_submissions(course_key, item_location, 'openassessment'),
            key=lambda x: x['created_at']
        )

        if not submissions:
            return [], [], []

        # Find rubric
        rubric = {}
        find_rubric = False
        for submission in submissions:
            assessments = Assessment.objects.filter(submission_uuid=submission['uuid']).select_related('rubric')
            for assessment in assessments:
                rubric = RubricSerializer.serialized_from_cache(assessment.rubric)
                find_rubric = True
                break
            if find_rubric:
                break

        for submission in submissions:
            user = user_by_anonymous_id(submission['student_id'])
            raw_answer = submission['answer']
            # Note: 'parts' is added as top-level domain of 'raw_answer' since Cypress
            # Currently, get only the first text from a list of answer parts
            answer_text = raw_answer['parts'][0]['text'] if 'parts' in raw_answer else raw_answer['text']
            latest_score = sub_api.get_latest_score_for_submission(submission['uuid'])

            row = [
                user.username,
                answer_text.replace('\n', '[\\n]'),
                submission['created_at'],
                AssessmentWorkflow.get_by_submission_uuid(submission['uuid']).status,
                latest_score['points_earned'] if latest_score is not None else '',
                latest_score['points_possible'] if latest_score is not None else '',
                latest_score['created_at'] if latest_score is not None else '',
            ]

            # Build peer assessment data. If not peer assessment, then always getting empty row
            peer_assessments = Assessment.objects.prefetch_related('parts').prefetch_related('rubric').filter(
                submission_uuid=submission['uuid'],
                score_type=PEER_TYPE
            ).order_by('scored_at')
            _header_extra, _row = cls._build_peer_assessment_cell(submission['uuid'], rubric, peer_assessments, user_by_anonymous_id)
            header_extra.extend(_header_extra)
            row.extend(_row)

            # Build staff assessment data
            staff_assessments = Assessment.objects.prefetch_related('parts').prefetch_related('rubric').filter(
                submission_uuid=submission['uuid'],
                score_type=STAFF_TYPE
            ).order_by('scored_at')
            _header_extra, _row = cls._build_staff_assessment_cell(rubric, staff_assessments, user_by_anonymous_id)
            header_extra.extend(_header_extra)
            row.extend(_row)

            rows.append(row)

        header.extend(sorted(set(header_extra), key=header_extra.index))
        return submissions, header, rows


# Note: modified from apps/openassessment/assessment/models/base.py Assessment.scores_by_criterion()
def scores_by_criterion(assessments):
    """Create a dictionary of lists for scores associated with criterion

    Create a key value in a dict with a list of values, for every criterion
    found in an assessment.

    Iterate over every part of every assessment. Each part is associated with
    a criterion name, which becomes a key in the score dictionary, with a list
    of scores.

    Args:
        assessments (list): List of assessments to sort scores by their
            associated criteria.

    Examples:
        >>> assessments = Assessment.objects.all()
        >>> scores_by_criterion(assessments)
        {
            "foo": [1, 2, 3],
            "bar": [6, 7, 8]
        }
    """
    assessments = list(assessments)  # Force us to read it all
    if not assessments:
        return {}

    scores = OrderedDict()

    for assessment in assessments:
        for part in assessment.parts.all().select_related('option__criterion').order_by('option__criterion__order_num'):
            criterion_name = part.option.criterion.name
            # Note: modified because non-ascii key makes defaultdict out of order.
            if criterion_name not in scores:
                scores[criterion_name] = [part.option.points]
            else:
                scores[criterion_name].append(part.option.points)

    return scores
