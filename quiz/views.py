from django.shortcuts import render
from django.contrib import messages
from news.models import SearchHistory

def quiz_view(request):
    quiz_question = None
    result_message = None

    if request.method == 'POST':
        user_guess = request.POST.get('user_guess', '')
        quiz_question = SearchHistory.get_random_quiz_question()

        if user_guess.lower() == quiz_question.search_query.lower():
            result_message = '맞혔습니다!'
            messages.success(request, result_message)
        else:
            result_message = '틀렸습니다.'
            messages.error(request, result_message)

    else:
        quiz_question = SearchHistory.get_random_quiz_question()

    context = {
        'quiz_question': quiz_question,
        'result_message': result_message,
    }

    return render(request, 'quiz/index.html', context)