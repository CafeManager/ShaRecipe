from flask import Flask, render_template, request, g, session, redirect, flash
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from form import UserAddForm, LoginForm, RecipeForm, IngredientEntryForm, StepEntryForm
from models import db, connect_db, User, Recipe, Step, Ingredient
from sqlalchemy.exc import IntegrityError
import requests
import datetime

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config["SECRET_KEY"] = "this-is-secr3t"

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///sharecipe"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config['DEBUG'] = True
API_KEY = "fc0a5c0a6ee744afacee96a81cf8664e"

connect_db(app)


@app.before_request
def add_user_to_g():
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    session[CURR_USER_KEY] = user.id


def do_logout():
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route("/")
def home_page():
    res = requests.get(
        "https://api.spoonacular.com/recipes/random",
        params={"apiKey": {API_KEY}, "tags": "dessert", "number": 5},
    )
    recipes = res.json().get("recipes")
    recipeList = [
        {
            "id": recipe.get("id"),
            "title": recipe.get("title"),
            "img": recipe.get("image"),
            "summary": [recipe.get("summary")],
        }
        for recipe in recipes
    ]
    print(recipes)

    return render_template("homepage.html", res=recipeList)


@app.route("/user/register", methods=["GET", "POST"])
def create_user():
    form = UserAddForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", "danger")
            return render_template("users/signup.html", form=form)

        do_login(user)

        return redirect("/")

    return render_template("user/register.html", form=form)


@app.route("/user/login", methods=["GET", "POST"])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            session[CURR_USER_KEY] = user.id
            return redirect("/")

    return render_template("user/login.html", form=form)


@app.route("/recipe/create")
def register_user():
    form = LoginForm()
    return render_template("recipe/create.html", form=form)


@app.route("/logout")
def logout():
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    return redirect("/")


@app.route("/fetchresults")
def fetch_results():
    q = request.args.get("q")
    res = requests.get(
        f"https://api.spoonacular.com/recipes/complexSearch?apiKey=fc0a5c0a6ee744afacee96a81cf8664e&query={q}"
    )
    json = res.json()
    idString = ",".join([str(s.get("id")) for s in json["results"]])
    idRes = requests.get(
        f"https://api.spoonacular.com/recipes/informationBulk?ids={idString}&apiKey={API_KEY}"
    )
    extraInfo = idRes.json()
    return render_template(
        "search_results.html",
        data={"recipeData": json["results"], "extraRecipeDataById": extraInfo},
    )


@app.route("/recipes/<int:id>/create", methods=['GET', 'POST'])
def get_recipe_template(id):
    res = requests.get(
        f"https://api.spoonacular.com/recipes/{id}/information?apiKey={API_KEY}"
    )
    json = res.json()
    

    ingredient_data = []
    steps_data = []
    

    for ingredient in json.get('extendedIngredients'):
        ingredient_form = IngredientEntryForm()
        ingredient_data.append({'amount': ingredient.get('amount'), 'unit':ingredient.get('unit'), 'name':ingredient.get('name')})
        ingredient_form.amount.data = ingredient.get('amount')
        ingredient_form.unit.data = ingredient.get('unit')
        ingredient_form.name.data = ingredient.get('name')
        # form.ingredients.append_entry(ingredient_form)

    for step in json.get('analyzedInstructions')[0].get('steps'):
        step_form = StepEntryForm()
        steps_data.append({'step': step.get('step')})
    form = RecipeForm(name=json.get('name'), total_time=json.get('readyInMinutes'), 
                      total_servings=json.get('total_servings'), summary=json.get('summary'), 
                      steps=steps_data, ingredients=ingredient_data)

    if form.validate_on_submit():
        name = form.name.data
        user_id = g.user.id
        created_at = datetime.datetime.now()
        created_by = g.user.id
        total_time = form.total_time.data
        parent_recipe_id = 0
        total_servings = form.total_servings.data
        api_id = id

        ingredient_json = {'ingredients':[]}
        step_json = {'steps':[]}
        

        for ingredient in form.ingredients:
            ingredient_json['ingredients'].append({
                'amount':ingredient.data['amount'],
                'unit':ingredient.data['unit'],
                'name':ingredient.data['name']
            })

        for step in form.steps:
            step_json['steps'].append({
                'step': step.step.data
            })



        recipe = Recipe(name=name, 
                        created_at=created_at, created_by=created_by, 
                        total_time=total_time, total_servings=total_servings, 
                        api_id=api_id, parent_recipe_id=parent_recipe_id)
        
        ingredient_list = Ingredient(json=ingredient_json, recipe_id=recipe.id)
        
        step_list = Step(json=step_json, recipe_id=recipe.id)

        recipe.ingredients.append(ingredient_list)
        recipe.steps.append(step_list)
        db.session.add(recipe)
        db.session.commit()
    else:
        print(form.errors)
        
        
        
    return render_template("/recipe/create.html", res=json, form=form)

    