"""
LLD: Service layer – business logic moved out of views for clarity and testability.
"""
from OTS.models import Candidate, Question, Result, MembershipPlan


def get_allowed_question_counts(candidate):
    """Return list of test sizes (e.g. [1, 3, 5]) this candidate is allowed to take. No plan = all allowed."""
    if not candidate or not candidate.membership_plan:
        return [1, 3, 5]
    return candidate.membership_plan.get_allowed_question_counts()


def evaluate_answer(question, user_answer_raw):
    """
    Strategy: check if user's answer is correct. Supports ans as letter (A/B/C/D) or as option text.
    Returns True if correct, False otherwise.
    """
    user_answer = (user_answer_raw or '').strip().upper()
    correct_ans = (question.ans or '').strip().upper()
    if correct_ans in ('A', 'B', 'C', 'D'):
        return user_answer == correct_ans
    option_to_letter = [
        (question.a, 'A'), (question.b, 'B'), (question.c, 'C'), (question.d, 'D')
    ]
    correct_letter = None
    for opt_text, letter in option_to_letter:
        if (opt_text or '').strip() == correct_ans or (opt_text or '').strip().upper() == correct_ans:
            correct_letter = letter
            break
    return correct_letter is not None and user_answer == correct_letter


def calculate_and_save_result(candidate_username, post_data):
    """
    Compute test result from POST data, save Result and update Candidate stats.
    Does not redirect; view handles redirect.
    """
    qid_list = []
    for k in post_data:
        if k.startswith('qno'):
            try:
                qid_list.append(int(post_data[k]))
            except (ValueError, TypeError):
                pass

    total_attempt = 0
    total_right = 0
    total_wrong = 0

    for n in qid_list:
        try:
            question = Question.objects.get(qid=n)
            user_answer = post_data.get('q' + str(n))
            if evaluate_answer(question, user_answer):
                total_right += 1
            else:
                total_wrong += 1
            total_attempt += 1
        except (KeyError, Question.DoesNotExist):
            pass

    points = (total_right - total_wrong) / len(qid_list) * 10 if qid_list else 0

    candidate = Candidate.objects.get(username=candidate_username)
    result = Result(
        username=candidate,
        attempt=total_attempt,
        right=total_right,
        wrong=total_wrong,
        points=points,
    )
    result.save()

    candidate.test_attempted += 1
    candidate.points = ((candidate.points * (candidate.test_attempted - 1)) + points) / candidate.test_attempted
    candidate.save()


def delete_candidate_account(username):
    """Delete candidate and all their results (cascade). No-op if candidate does not exist."""
    try:
        candidate = Candidate.objects.get(username=username)
        candidate.delete()
    except Candidate.DoesNotExist:
        pass


def assign_membership_plan(candidate_username, plan_id):
    """Assign plan to candidate. plan_id None or empty = remove plan. Returns True if candidate existed."""
    try:
        candidate = Candidate.objects.get(username=candidate_username)
        if plan_id:
            plan = MembershipPlan.objects.filter(pk=plan_id, is_active=True).first()
            candidate.membership_plan = plan
        else:
            candidate.membership_plan = None
        candidate.save()
        return True
    except (ValueError, Candidate.DoesNotExist):
        return False


def authenticate_candidate(username, password):
    """Return Candidate if credentials match, else None."""
    candidate = Candidate.objects.filter(username=username).first()
    if candidate and candidate.password == password:
        return candidate
    return None


def register_candidate(username, password, name, plan_id=None):
    """
    Register a new candidate. Returns (success: bool, user_status: int).
    user_status: 1 = username exists, 2 = created, 3 = invalid (e.g. not POST).
    """
    if Candidate.objects.filter(username=username).exists():
        return False, 1
    plan = None
    if plan_id:
        plan = MembershipPlan.objects.filter(pk=plan_id, is_active=True).first()
    candidate = Candidate(username=username, password=password, name=name, membership_plan=plan)
    candidate.save()
    return True, 2
