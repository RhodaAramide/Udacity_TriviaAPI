from importlib import resources

import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from sqlalchemy.sql.functions import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# define paginated questions
def paginate_questions(request, selection):
    current_questions = []
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/*": {"origins": "*"}})
    """
    Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response
    """
    
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route("/categories")
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        
        categories_dict =  {
                category.id: category.type for category in categories    
                }      
        
        if(len(categories) == 0):
            abort(404)
            
        return jsonify(
            {
                "success": True,
                "categories": categories_dict
            }
        )


    """
    
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.order_by(Category.id).all()
        categories_dict =  {
                category.id: category.type for category in categories    
                }        
        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "categories": categories_dict,
                "current_category": None
            }
        )
        
    """    
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            
            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,                    
                }
            )

        except:
            abort(422)
    """
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    
    Merged the two requests
    """
    @app.route("/questions", methods=['POST'])
    def search_questions():
        body = request.get_json()
        search = body.get('searchTerm', None)
        
        if search != None:
            question = Question.query.filter(Question.question.contains(f'{search}')).all()
            question_dict = [obj.format() for obj in question]
            
            return jsonify ({
                'questions': question_dict,
                'total_questions': len(question),
                })
        else:
            question = body.get('question', None)
            answer = body.get('answer', None)
            category = body.get('category', None)
            difficulty = body.get('difficulty', None)
            
            question_obj = Question(question=question, answer=answer, category=category, difficulty=difficulty)
            question_obj.insert()
            
            return jsonify({
                "success": True
            })
                
    
    """    
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def questions_by_category(category_id):
        category = Category.query.get((category_id))
        selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)

        if category is None:
            abort(404)
        
        return jsonify(
            {
                "success": True,                
                "questions": current_questions,
                "total_questions": len(selection),
                "current_category": category_id
            }
        )

    """    
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route("/quizzes", methods=['POST'])
    def get_quiz():
        body = request.get_json()
        try:          
           if body:
                previous_questions = body["previous_questions"]
                quiz_category = body["quiz_category"]
                
                if quiz_category:
                    questions = Question.query.filter_by(category=quiz_category).filter(~Question.id.in_(
                        previous_questions)).order_by(random()).all()
                else:
                    questions = Question.query.filter(~Question.id.in_(
                        previous_questions)).order_by(random()).all()    
                if len(questions) > 0:
                    question_dict = {obj.format() for obj in questions}                     
                else:
                    question_dict = None
                    
                return jsonify({
                    'success': True,
                    'question': question_dict                   
                })
        except:
            abort(400)           
        
        
    """    
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )

    return app

