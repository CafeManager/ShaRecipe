from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, FieldList, FormField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField("Username", validators=[DataRequired()])
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Length(min=6)])
    image_url = StringField("(Optional) Image URL")


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[Length(min=6)])


class ProfileForm(FlaskForm):
    """Profile form."""

    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    image_url = StringField("(Optional) Image URL")
    header_image_url = StringField("(Optional) Header Image URL")
    bio = StringField("(Optional) Bio")
    password = PasswordField(validators=[DataRequired()])

class IngredientEntryForm(FlaskForm):
    amount = FloatField("Amount")
    unit = StringField("Unit", validators=[Optional()])
    name = StringField("Name")

class StepEntryForm(FlaskForm):
    step = StringField("Step")

class RecipeForm(FlaskForm):
    """Profile form."""
    name = StringField("Edit a title")
    total_time = IntegerField("Edit recipe time")
    total_servings = IntegerField("Edit serving amount")
    summary = StringField("Summary")
    ingredients = FieldList(FormField(IngredientEntryForm), min_entries=1)
    steps = FieldList(FormField(StepEntryForm), min_entries=1)
    

    
