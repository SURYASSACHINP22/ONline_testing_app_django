from django.shortcuts import render
from django.template import loader
from django.http import HttpResponseRedirect,HttpResponse
from OTS.models import *
import random

# Create your views here.

def welcome(request):
    template = loader.get_template('welcome.html')
    return HttpResponse(template.render())




def candidateRegistrationForm(request):
    res = render(request,'registration_Form.html')
    return res




# def candidateRegistration(request):
#     if request.method =='POST':
#         username = request.POST['username']
#         # Check if the username already exists
#         if(len(Candidate.objects.filter(username=username))==0):
#             userStatus = 1
#             context = {
#                 'userStatus': userStatus,
#             }
#         else:
#             candidate =Candidate()
#             candidate.username = username
#             candidate.password = request.POST.get('password')
#             candidate.name = request.POST['name']
#             # candidate.test_attempted = 0
#             # candidate.points = 0.0
#             candidate.save()
#             userStatus = 2
#             context = {
#                 'userStatus': userStatus,
#             }
#             return render(request, 'registration.html', context)
#     else:
#         # Handle the case when the request method is not POST
#         # You can return an error message or redirect to another page
#         userStatus = 3
#         context = {
#             'userStatus': userStatus,
#         }
#         return render(request, 'registration.html', context)
    




def candidateRegistration(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Safely retrieve the username

        # Check if the username already exists
        if Candidate.objects.filter(username=username).exists():
            userStatus = 1  # Username already registered
        else:
            candidate = Candidate()
            candidate.username = username
            candidate.password = request.POST.get('password')  # Hash if needed
            candidate.name = request.POST.get('name')
            candidate.save()
            userStatus = 2  # Registration successful

        # Send appropriate context to the template
        context = {
            'userStatus': userStatus,
        }
        return render(request, 'registration.html', context)
    else:
        userStatus = 3  # Invalid request method
        context = {
            'userStatus': userStatus,
        }
        return render(request, 'registration.html', context)






def loginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Use .get() for safety
        password = request.POST.get('password')

        candidate = Candidate.objects.filter(username=username).first()
        if candidate and candidate.password == password:  # Match password securely
            # Login success - establish session
            request.session['username'] = candidate.username
            request.session['name'] = candidate.name
            return HttpResponseRedirect("home")
        else:
            # Invalid username or password
            loginError = "Invalid username or password"
            context = {
                'loginError': loginError,
            }
            return render(request, 'login.html', context)
    else:
        return render(request, 'login.html')


    

# def loginView(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         candidate = Candidate.objects.get(username=username, password=password)
#         if len(candidate) == 0:
#             loginError = "Invalid username or password"
#             context = {
#                 'loginError': loginError,
#             }
#             return render(request, 'login.html', context)
#         else:
#             #loginsuccess so we will make a session for the user
#             request.session['username'] = candidate[0].username
#             request.session['name'] = candidate[2].name
#             return HttpResponseRedirect("home")
#     else:   
#         res =render(request, 'login.html')
#         return res  




def candidateHome(request):
    # Check if the user is logged in by checking the session just make full migrate and run the server not migration
    if 'name' and 'username' not in request.session:
        res = HttpResponseRedirect("login")
    else:
        res = render(request, 'home.html')
    return res 

        




def testPaper(request):
    if 'name' and 'username' not in request.session:
        res = HttpResponseRedirect("login")
    n = int(request.GET.get('n'))
    question_pool = list(Question.objects.all())
    random.shuffle(question_pool)
    questions_list = question_pool[:n]

    context = {
        'questions': questions_list,
    }
    return render(request, 'test_paper.html', context)






# def calculateTestResult(request):
#     if 'name' and 'username' not in request.session:
#         res = HttpResponseRedirect("login")
#     total_attempt = 0
#     total_right = 0
#     total_wrong = 0
#     qid_list = []
#     for k in request.POST:
#         if k.startswith('qno'):
#             qid_list.append(int(request.POST[k]))
#     for n in qid_list:
#         question = Question.objects.get(qid=n)
#         try:
#             if question.ans == request.POST['q'+str(n)]:
#                 total_right += 1
#             else:
#                 total_wrong += 1
#             total_attempt += 1
#         except:
#             pass
#     points = (total_right - total_wrong)/len(qid_list) * 10

#     result=Result()
#     ## Update the candidate's test_attempted and points in the Candidate model
#     #username irs the foreign key in the Result model so we have to get the candidate object first
#     result.username = Candidate.objects.get(username=request.session['username'])
#     result.attempt = total_attempt
#     result.right = total_right
#     result.wrong = total_wrong
#     result.points = points
#     result.save()
#     #now we have to update the candidate model also 
#     candidate = Candidate.objects.get(username = request.session['username'])
#     candidate.test_attempted += 1
#     candidate.points += candidate.points*((candidate.test_attempted-1)+points)/candidate.test_attempted
#     candidate.save()  
#     return HttpResponseRedirect("result") 
 




def calculateTestResult(request):
    if 'name' not in request.session or 'username' not in request.session:
        return HttpResponseRedirect("login")

    total_attempt = 0
    total_right = 0
    total_wrong = 0
    qid_list = []

    for k in request.POST:
        if k.startswith('qno'):
            qid_list.append(int(request.POST[k]))

    for n in qid_list:
        try:
            question = Question.objects.get(qid=n)
            if question.ans == request.POST['q' + str(n)]:
                total_right += 1
            else:
                total_wrong += 1
            total_attempt += 1
        except KeyError:
            pass
        except Question.DoesNotExist:
            pass

    if len(qid_list) == 0:
        points = 0
    else:
        points = (total_right - total_wrong) / len(qid_list) * 10

    # Save the result in the Result model
    result = Result()
    result.username = Candidate.objects.get(username=request.session['username'])
    result.attempt = total_attempt
    result.right = total_right
    result.wrong = total_wrong
    result.points = points
    result.save()

    # Update the candidate model
    candidate = Candidate.objects.get(username=request.session['username'])
    candidate.test_attempted += 1
    candidate.points = ((candidate.points * (candidate.test_attempted - 1)) + points) / candidate.test_attempted
    candidate.save()
    # return HttpResponseRedirect(reverse('OTS:showTestResult'))
    return HttpResponseRedirect("result") 




def testResultHistory(request):
    if 'name' and 'username' not in request.session:
        res = HttpResponseRedirect("login")
    candidate = Candidate.objects.get(username=request.session['username'])
    #result = Result.objects.filter(username_id=candidate[0].username)
    # context = {
    #     'candidate': candidate[0],
    #     'results': results,
    # }
    
    results = Result.objects.filter(username=candidate)
    context = {
        'candidate': candidate,
        'results': results,
    }
    return render(request, 'candidate_history.html', context)







def showTestResult(request):
    if 'name' not in request.session or 'username' not in request.session:
        return HttpResponseRedirect("login")
    
    try:
        latest_result = Result.objects.latest('resultid')
        results = Result.objects.filter(resultid=latest_result.resultid, username__username=request.session['username'])  # Match foreign key
    except Result.DoesNotExist:
        results = None

    context = {
        'results': results,
    }
    return render(request, 'show_result.html', context)


# def showTestResult(request):
#     if 'name' and 'username' not in request.session:
#         res = HttpResponseRedirect("login")
#     result = Result.objects.filter(resultid = Result.objects.latest('resultid').resultid,username_id=request.session['username'])
#     context = {         
#         'result': result,
#     }   
#     return render(request, 'show_result.html', context)





def logoutView(request):
    if 'name' and 'username'  in request.session:
        del request.session['name']
        del request.session['username']
    res = HttpResponseRedirect("login")
    return res
    
