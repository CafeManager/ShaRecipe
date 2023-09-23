from flask import Flask, render_template, request, g, session, redirect, flash
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from form import UserAddForm, LoginForm, RecipeForm, IngredientEntryForm, StepEntryForm
from models import db, connect_db, User, Recipe, Step, Ingredient
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup
import requests
import datetime
from jsondiff import diff
from bs4 import BeautifulSoup
import os

CURR_USER_KEY = "curr_user"

# initiate the application
def create_app():
    app = Flask(__name__)
    
    # check for a database url connection string
    # use sharecipe by default
    if os.getenv("DATABASE_URL", default=None) is not None:
        print( os.getenv("DATABASE_URL"))
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///sharecipe"
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = "this-is-secr3t"
    connect_db(app)
    return app

# start the app
app = create_app()

API_KEY = "ebc68d98ecfa4ecba9276fcd02a7660a"

connect_db(app)

# before a request is processed, create a global variable that is the user's data
@app.before_request
def add_user_to_g():
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

# give the client a user id to remember
def do_login(user):
    session[CURR_USER_KEY] = user.id

# clear the session data so the user data not accessible anymore
def do_logout():
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route("/", methods=["GET", "POST"])
def home_page():
    q = request.args.get("q")
    # check if there is something currently being searched
    if q:
        #send a request based on the search parameter
        res = requests.get(
            f"https://api.spoonacular.com/recipes/complexSearch?apiKey={API_KEY}&query={q}"
        )
        json = res.json()
        idString = ",".join([str(s.get("id")) for s in json["results"]])
        idRes = requests.get(
            f"https://api.spoonacular.com/recipes/informationBulk?ids={idString}&apiKey={API_KEY}"
        )
        extraInfo = idRes.json()
        recipeList = [
            {
                "id": recipe.get("id"),
                "title": recipe.get("title"),
                "img": recipe.get("image"),
                "summary": BeautifulSoup(
                    recipe.get("summary"), features="html.parser"
                ).get_text(),
            }
            for recipe in extraInfo
        ]
        # render the homepage with search results
        return render_template("homepage.html", res=recipeList)
    else:
        # render the homepage with no recipes
        return render_template("homepage.html", res=[])


# user signup
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

# user login
@app.route("/user/login", methods=["GET", "POST"])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            session[CURR_USER_KEY] = user.id
            return redirect("/")

    return render_template("user/login.html", form=form)


# show a user's profile
@app.route("/user/<int:id>", methods=["GET", "POST"])
def show_profile(id):
    user = User.query.get_or_404(id)
    recipes = Recipe.query.filter(user.username == Recipe.created_by).all()

    return render_template("user/profile.html", recipes=recipes)

@app.route("/recipe/create")
def register_user():
    form = LoginForm()
    return render_template("recipe/create.html", form=form)

# remove user data from session then send to homepage
@app.route("/logout")
def logout():
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    return redirect("/")

# go to recipe creation page
@app.route("/recipes/<int:id>/create", methods=["GET", "POST"])
def get_recipe_template(id):
    # start with a recipe based on a recipe from spoonacular API
    res = requests.get(
        f"https://api.spoonacular.com/recipes/{id}/information?apiKey={API_KEY}"
    )
    json = res.json()

    # strip html tags
    json["summary"] = BeautifulSoup(
        json.get("summary"), features="html.parser"
    ).get_text()
    ingredient_data = []
    steps_data = []

    for ingredient in json.get("extendedIngredients"):
        ingredient_form = IngredientEntryForm()
        ingredient_data.append(
            {
                "amount": ingredient.get("amount"),
                "unit": ingredient.get("unit"),
                "name": ingredient.get("name"),
            }
        )
        ingredient_form.amount.data = ingredient.get("amount")
        ingredient_form.unit.data = ingredient.get("unit")

    for step in json.get("analyzedInstructions")[0].get("steps"):
        step_form = StepEntryForm()
        steps_data.append({"step": step.get("step")})

    stripped_summary = BeautifulSoup(
        json.get("summary"), features="html.parser"
    ).get_text()
    form = RecipeForm(
        title=json.get("title"),
        image_url=json.get("image"),
        total_time=json.get("readyInMinutes"),
        total_servings=json.get("servings"),
        summary=stripped_summary,
        steps=steps_data,
        ingredients=ingredient_data,
    )

    if form.validate_on_submit():
        title = form.title.data
        summary = form.summary.data
        image_url = form.image_url.data
        created_at = datetime.datetime.now()
        created_by = g.user.username
        total_time = form.total_time.data
        parent_recipe_id = 0
        total_servings = form.total_servings.data
        api_id = id

        ingredient_json = {"ingredients": []}
        step_json = {"steps": []}

        for ingredient in form.ingredients:
            ingredient_json["ingredients"].append(
                {
                    "amount": ingredient.data["amount"],
                    "unit": ingredient.data["unit"],
                    "name": ingredient.data["name"],
                }
            )

        for step in form.steps:
            step_json["steps"].append({"step": step.step.data})

        recipe = Recipe(
            title=title,
            summary=summary,
            image_url=image_url,
            created_at=created_at,
            created_by=created_by,
            total_time=total_time,
            total_servings=total_servings,
            api_id=api_id,
            parent_recipe_id=parent_recipe_id,
        )

        ingredient_list = Ingredient(json=ingredient_json, recipe_id=recipe.id)

        step_list = Step(json=step_json, recipe_id=recipe.id)

        recipe.ingredients.append(ingredient_list)
        recipe.steps.append(step_list)
        db.session.add(recipe)
        db.session.commit()

        return redirect(f"/user/{g.user.id}")
    else:
        print(form.errors)

    return render_template("/recipe/create.html", res=json, form=form)


# show a recipe within the database
@app.route("/recipes/<int:id>")
def show_recipe_template(id):
    recipe = Recipe.query.get_or_404(id)

    return render_template("/recipe/show.html", recipe=recipe)

# say the differences between 2 recipe lists
def get_ingredient_differences(ingredient_list_1, ingredient_list_2):
    curr_recipe_len = len(ingredient_list_1)
    next_recipe_len = len(ingredient_list_2)
    ingredient_diff = []
    (higher_rec, highest_recipe_len) = (
        ("curr", curr_recipe_len)
        if curr_recipe_len >= next_recipe_len
        else ("next", next_recipe_len)
    )
    for i in range(highest_recipe_len):
        if higher_rec == "curr":
            curr_ingredient = ingredient_list_1[i]

            if i < next_recipe_len:
                next_ingredient = ingredient_list_2[i]
                if curr_ingredient == next_ingredient:
                    continue
                else:
                    ingredient_diff.append(
                        {
                            "location": i,
                            "type": "changed",
                            "content": {
                                "next_ingredient": next_ingredient,
                                "curr_ingredient": curr_ingredient,
                            },
                        }
                    )
            else:
                ingredient_diff.append(
                    {"location": i, "type": "added", "content": curr_ingredient}
                )
        elif higher_rec == "next":
            next_ingredient = ingredient_list_2[i]
            if i < curr_recipe_len:
                curr_ingredient = ingredient_list_1[i]
                if curr_ingredient == next_ingredient:
                    continue
                else:
                    ingredient_diff.append(
                        {
                            "location": i,
                            "type": "changed",
                            "content": {
                                "next_ingredient": next_ingredient,
                                "curr_ingredient": curr_ingredient,
                            },
                        }
                    )
            else:
                ingredient_diff.append(
                    {"location": i, "type": "deleted", "content": next_ingredient}
                )
    return ingredient_diff

# show recipe history page
@app.route("/recipes/<int:id>/history")
def show_recipe_history(id):
    root_recipe = Recipe.query.get_or_404(id)
    curr_recipe = root_recipe

    recipeList = []
    change_list = []
    ingredient_change_list = []
    changes = []
    change_count = 0
    recipeList.append(root_recipe)
    while curr_recipe.parent_recipe_id != 0:
        change_count += 1
        next_recipe = Recipe.query.get(curr_recipe.parent_recipe_id)
        curr_recipe_len = len(curr_recipe.steps[0].json.get("steps"))
        next_recipe_len = len(next_recipe.steps[0].json.get("steps"))
        ingredientDiff = diff(
            next_recipe.ingredients[0].json,
            curr_recipe.ingredients[0].json,
            syntax="explicit",
        )
        step_diff = []
        (higher_rec, highest_recipe_len) = (
            ("curr", curr_recipe_len)
            if curr_recipe_len >= next_recipe_len
            else ("next", next_recipe_len)
        )
        for i in range(highest_recipe_len):
            if higher_rec == "curr":
                curr_step = curr_recipe.steps[0].json.get("steps")[i]["step"]

                if i < next_recipe_len:
                    next_step = next_recipe.steps[0].json.get("steps")[i]["step"]
                    if curr_step == next_step:
                        continue
                    else:
                        step_diff.append(
                            {
                                "location": i,
                                "type": "changed",
                                "content": {
                                    "next_step": next_step,
                                    "curr_step": curr_step,
                                },
                            }
                        )
                else:
                    step_diff.append(
                        {"location": i, "type": "added", "content": curr_step}
                    )
            elif higher_rec == "next":
                next_step = next_recipe.steps[0].json.get("steps")[i]["step"]
                if i < curr_recipe_len:
                    curr_step = curr_recipe.steps[0].json.get("steps")[i]["step"]
                    if curr_step == next_step:
                        continue
                    else:
                        step_diff.append(
                            {
                                "location": i,
                                "type": "changed",
                                "content": {
                                    "next_step": next_step,
                                    "curr_step": curr_step,
                                },
                            }
                        )
                else:
                    step_diff.append(
                        {"location": i, "type": "deleted", "content": next_step}
                    )
        change_list.append(step_diff)
        curr_recipe = next_recipe
        curr_recipe = next_recipe
        next_recipe = Recipe.query.get(curr_recipe.parent_recipe_id)

    curr_recipe_2 = root_recipe
    while curr_recipe_2.parent_recipe_id != 0:
        next_recipe2 = Recipe.query.get(curr_recipe_2.parent_recipe_id)

        ingredient_differences = get_ingredient_differences(
            curr_recipe_2.ingredients[0].json.get("ingredients"),
            next_recipe2.ingredients[0].json.get("ingredients"),
        )
        ingredient_change_list.append(ingredient_differences)
        curr_recipe_2 = next_recipe2
    changes = {
        "step_differences": change_list,
        "ingredient_differences": ingredient_change_list,
    }

    return render_template("/recipe/history.html", changes=changes)

# update a recipe
@app.route("/recipes/<int:id>/update", methods=["GET", "POST"])
def update_recipe_template(id):
    recipe = Recipe.query.get_or_404(id)

    ingredient_data = []
    steps_data = []

    for ingredient in recipe.ingredients[0].json.get("ingredients"):
        ingredient_data.append(
            {
                "amount": ingredient.get("amount"),
                "unit": ingredient.get("unit"),
                "name": ingredient.get("name"),
            }
        )

    for step in recipe.steps[0].json.get("steps"):

        steps_data.append({"step": step.get("step")})

    form = RecipeForm(
        title=recipe.title,
        image_url=recipe.image_url,
        total_time=recipe.total_time,
        total_servings=recipe.total_servings,
        summary=recipe.summary,
        steps=steps_data,
        ingredients=ingredient_data,
    )

    if form.validate_on_submit():
        title = form.title.data
        summary = form.summary.data
        image_url = form.image_url.data
        created_at = datetime.datetime.now()
        created_by = g.user.username
        total_time = form.total_time.data
        parent_recipe_id = id
        total_servings = form.total_servings.data
        api_id = id

        ingredient_json = {"ingredients": []}
        step_json = {"steps": []}

        for ingredient in form.ingredients:
            ingredient_json["ingredients"].append(
                {
                    "amount": ingredient.data["amount"],
                    "unit": ingredient.data["unit"],
                    "name": ingredient.data["name"],
                }
            )

        for step in form.steps:
            step_json["steps"].append({"step": step.step.data})

        recipe = Recipe(
            title=title,
            summary=summary,
            image_url=image_url,
            created_at=created_at,
            created_by=created_by,
            total_time=total_time,
            total_servings=total_servings,
            api_id=api_id,
            parent_recipe_id=parent_recipe_id,
        )

        ingredient_list = Ingredient(json=ingredient_json, recipe_id=recipe.id)

        step_list = Step(json=step_json, recipe_id=recipe.id)

        recipe.ingredients.append(ingredient_list)
        recipe.steps.append(step_list)
        db.session.add(recipe)
        db.session.commit()

        return redirect(f"/user/{g.user.id}")
    else:
        print(form.errors)

    return render_template("/recipe/update.html", recipe=recipe, form=form)
