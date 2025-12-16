from main.models import User, StudentEvaluation

user = User.objects.get(username='jzapata')
evals = StudentEvaluation.objects.filter(faculty=user)

print(f'\n=== Student Evaluations for {user.username} ===')
print(f'Total evaluations: {evals.count()}\n')

if evals.count() > 0:
    print('Comments found:')
    for i, eval in enumerate(evals, 1):
        if eval.comments:
            print(f'{i}. "{eval.comments}"')
        else:
            print(f'{i}. (No comment - empty)')
else:
    print('No evaluations found')
