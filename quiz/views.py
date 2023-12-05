from django.shortcuts import render
from news.models import SearchHistory

def quiz_view(request):
    if request.method == 'POST':
        user_guess = request.POST.get('user_guess', '')
        
        # Retrieve the correct quiz question before displaying the result
        correct_quiz_question = SearchHistory.get_random_quiz_question()

        if user_guess.lower() == correct_quiz_question.search_query.lower():
            result_message = '맞혔습니다!'
        else:
            result_message = f'틀렸습니다. 정답은 {correct_quiz_question.search_query}입니다.'

        context = {
            'result_message': result_message,
            'correct_answer': correct_quiz_question.search_query,
        }

        return render(request, 'quiz/index.html', context)

    else:
        quiz_question = SearchHistory.get_random_quiz_question()

        context = {
            'quiz_question': quiz_question,
        }

        return render(request, 'quiz/index.html', context)