from __future__ import annotations

from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

from .utils import ELECTRICITY_PROVIDER_CHOICES


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Stay signed in")
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class ReminderForm(FlaskForm):
    name = StringField("Reminder title", validators=[DataRequired(), Length(max=140)])
    category = SelectField(
        "Type",
        choices=[
            ("medicine", "Medicine"),
            ("doctor", "Doctor Appointment"),
            ("vaccination", "Vaccination"),
            ("inspection", "System Inspection"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    due_date = DateField("Date", validators=[DataRequired()], format="%Y-%m-%d")
    due_time = TimeField("Time", validators=[DataRequired()], format="%H:%M")
    detail = TextAreaField("Details", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save reminder")


class ProjectForm(FlaskForm):
    name = StringField("Project / Site name", validators=[DataRequired(), Length(max=160)])
    installer = StringField("Installer / Vendor", validators=[Optional(), Length(max=160)])
    system_type = SelectField(
        "System type",
        choices=[
            ("on-grid", "On-grid (Net Metering)"),
            ("off-grid", "Off-grid (Battery)"),
            ("hybrid", "Hybrid"),
            ("shared", "Community / Shared"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    installation_date = DateField(
        "Installation date", validators=[Optional()], format="%Y-%m-%d", default=date.today
    )
    detail = TextAreaField("Project details / Notes", validators=[Optional()])
    image = FileField(
        "Upload site photo", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"])]
    )
    submit = SubmitField("Save project")


class HealthStatForm(FlaskForm):
    label = StringField("Metric", validators=[DataRequired(), Length(max=120)])
    value = StringField("Value", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Save metric")


class HealthLogForm(FlaskForm):
    note = TextAreaField("Observation", validators=[DataRequired()])
    submit = SubmitField("Log update")


class ProfileForm(FlaskForm):
    name = StringField("Full name", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone number", validators=[Optional(), Length(max=30)])
    dob = DateField("Date of birth", validators=[Optional()], format="%Y-%m-%d")
    submit = SubmitField("Save profile")


class SubsidyNumbersForm(FlaskForm):
    roof_area = DecimalField(
        "Usable rooftop area (m²)",
        validators=[DataRequired(message="Please enter the usable rooftop area.")],
        places=2,
        rounding=None,
    )
    monthly_bill = DecimalField(
        "Average monthly electricity bill (₹)",
        validators=[
            DataRequired(message="Please enter your average monthly electricity bill."),
            NumberRange(min=100, message="Monthly bill should be at least ₹100 to run the estimate."),
        ],
        places=2,
        rounding=None,
    )
    provider = SelectField(
        "Electricity provider / DISCOM",
        choices=ELECTRICITY_PROVIDER_CHOICES,
        validators=[DataRequired(message="Select your electricity provider.")],
    )
    submit = SubmitField("Next: Preview savings")


class SubsidySiteForm(FlaskForm):
    state = SelectField(
        "State / Union Territory",
        choices=[
            ("", "Select"),
            ("Andhra Pradesh", "Andhra Pradesh"),
            ("Arunachal Pradesh", "Arunachal Pradesh"),
            ("Assam", "Assam"),
            ("Bihar", "Bihar"),
            ("Chhattisgarh", "Chhattisgarh"),
            ("Goa", "Goa"),
            ("Gujarat", "Gujarat"),
            ("Haryana", "Haryana"),
            ("Himachal Pradesh", "Himachal Pradesh"),
            ("Jharkhand", "Jharkhand"),
            ("Karnataka", "Karnataka"),
            ("Kerala", "Kerala"),
            ("Madhya Pradesh", "Madhya Pradesh"),
            ("Maharashtra", "Maharashtra"),
            ("Manipur", "Manipur"),
            ("Meghalaya", "Meghalaya"),
            ("Mizoram", "Mizoram"),
            ("Nagaland", "Nagaland"),
            ("Odisha", "Odisha"),
            ("Punjab", "Punjab"),
            ("Rajasthan", "Rajasthan"),
            ("Sikkim", "Sikkim"),
            ("Tamil Nadu", "Tamil Nadu"),
            ("Telangana", "Telangana"),
            ("Tripura", "Tripura"),
            ("Uttar Pradesh", "Uttar Pradesh"),
            ("Uttarakhand", "Uttarakhand"),
            ("West Bengal", "West Bengal"),
            ("Andaman and Nicobar Islands", "Andaman and Nicobar Islands"),
            ("Chandigarh", "Chandigarh"),
            ("Dadra and Nagar Haveli and Daman and Diu", "Dadra and Nagar Haveli and Daman and Diu"),
            ("Delhi", "Delhi"),
            ("Jammu and Kashmir", "Jammu and Kashmir"),
            ("Ladakh", "Ladakh"),
            ("Lakshadweep", "Lakshadweep"),
            ("Puducherry", "Puducherry"),
        ],
        validators=[DataRequired(message="Please select a state or union territory.")],
    )
    consumer_segment = SelectField(
        "Consumer type",
        choices=[
            ("residential", "Residential"),
            ("agricultural", "Agricultural"),
            ("community", "Community / cooperative"),
        ],
        validators=[DataRequired()],
    )
    grid_connection = SelectField(
        "Grid connection status",
        choices=[("grid", "Grid-connected"), ("off-grid", "Off-grid / unreliable")],
        validators=[DataRequired()],
    )
    roof_type = SelectField(
        "Roof type",
        choices=[
            ("", "Select roof type"),
            ("concrete-rcc", "Concrete (RCC)"),
            ("tin-metal", "Tin / Metal"),
            ("tiles", "Tiles"),
            ("asbestos", "Asbestos"),
            ("flat-roof", "Flat roof"),
            ("sloped-roof", "Sloped roof"),
            ("other", "Other"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Check eligibility & estimate")


class TrackerEntryForm(FlaskForm):
    entry_type = SelectField(
        "Entry type",
        choices=[
            ("generation", "Generation"),
            ("consumption", "Consumption"),
            ("export", "Export"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    kwh = DecimalField("kWh", validators=[DataRequired()], places=2, rounding=None)
    revenue = DecimalField("Monetary value (₹)", validators=[Optional()], places=2, rounding=None)
    panel_id = StringField("Panel ID", validators=[Optional(), Length(max=120)])
    date = DateField("Entry date", validators=[DataRequired()])
    note = TextAreaField("Note", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save entry")

