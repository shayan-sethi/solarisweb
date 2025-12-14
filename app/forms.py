from __future__ import annotations

from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from flask_babel import lazy_gettext as _l
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
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember = BooleanField(_l("Stay signed in"))
    submit = SubmitField(_l("Sign in"))


class RegisterForm(FlaskForm):
    name = StringField(_l("Full name"), validators=[Length(max=120)])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        _l("Confirm password"),
        validators=[DataRequired(), EqualTo("password", message=_l("Passwords must match."))],
    )
    submit = SubmitField(_l("Create account"))


class ReminderForm(FlaskForm):
    name = StringField(_l("Reminder title"), validators=[DataRequired(), Length(max=140)])
    category = SelectField(
        _l("Type"),
        choices=[
            ("medicine", _l("Medicine")),
            ("doctor", _l("Doctor Appointment")),
            ("vaccination", _l("Vaccination")),
            ("inspection", _l("System Inspection")),
            ("other", _l("Other")),
        ],
        validators=[DataRequired()],
    )
    due_date = DateField(_l("Date"), validators=[DataRequired()], format="%Y-%m-%d")
    due_time = TimeField(_l("Time"), validators=[DataRequired()], format="%H:%M")
    detail = TextAreaField(_l("Details"), validators=[Optional(), Length(max=1000)])
    submit = SubmitField(_l("Save reminder"))


class ProjectForm(FlaskForm):
    name = StringField(_l("Project / Site name"), validators=[DataRequired(), Length(max=160)])
    installer = StringField(_l("Installer / Vendor"), validators=[Optional(), Length(max=160)])
    system_type = SelectField(
        _l("System type"),
        choices=[
            ("on-grid", _l("On-grid (Net Metering)")),
            ("off-grid", _l("Off-grid (Battery)")),
            ("hybrid", _l("Hybrid")),
            ("shared", _l("Community / Shared")),
            ("other", _l("Other")),
        ],
        validators=[DataRequired()],
    )
    installation_date = DateField(
        _l("Installation date"), validators=[Optional()], format="%Y-%m-%d", default=date.today
    )
    detail = TextAreaField(_l("Project details / Notes"), validators=[Optional()])
    image = FileField(
        _l("Upload site photo"), validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"])]
    )
    submit = SubmitField(_l("Save project"))


class HealthStatForm(FlaskForm):
    label = StringField(_l("Metric"), validators=[DataRequired(), Length(max=120)])
    value = StringField(_l("Value"), validators=[DataRequired(), Length(max=120)])
    submit = SubmitField(_l("Save metric"))


class HealthLogForm(FlaskForm):
    note = TextAreaField(_l("Observation"), validators=[DataRequired()])
    submit = SubmitField(_l("Log update"))


class ProfileForm(FlaskForm):
    name = StringField(_l("Full name"), validators=[Optional(), Length(max=120)])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    phone = StringField(_l("Phone number"), validators=[Optional(), Length(max=30)])
    dob = DateField(_l("Date of birth"), validators=[Optional()], format="%Y-%m-%d")
    submit = SubmitField(_l("Save profile"))


class SubsidyNumbersForm(FlaskForm):
    roof_area = DecimalField(
        _l("Usable rooftop area (m²)"),
        validators=[DataRequired(message=_l("Please enter the usable rooftop area."))],
        places=2,
        rounding=None,
    )
    monthly_bill = DecimalField(
        _l("Average monthly electricity bill (₹)"),
        validators=[
            DataRequired(message=_l("Please enter your average monthly electricity bill.")),
            NumberRange(min=100, message=_l("Monthly bill should be at least ₹100 to run the estimate.")),
        ],
        places=2,
        rounding=None,
    )
    provider = SelectField(
        _l("Electricity provider / DISCOM"),
        choices=ELECTRICITY_PROVIDER_CHOICES,
        validators=[DataRequired(message=_l("Select your electricity provider."))],
    )
    submit = SubmitField(_l("Next: Preview savings"))


class SubsidySiteForm(FlaskForm):
    state = SelectField(
        _l("State / Union Territory"),
        choices=[
            ("", _l("Select")),
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
        validators=[DataRequired(message=_l("Please select a state or union territory."))],
    )
    consumer_segment = SelectField(
        _l("Consumer type"),
        choices=[
            ("residential", _l("Residential")),
            ("agricultural", _l("Agricultural")),
            ("community", _l("Community / cooperative")),
        ],
        validators=[DataRequired()],
    )
    grid_connection = SelectField(
        _l("Grid connection status"),
        choices=[("grid", _l("Grid-connected")), ("off-grid", _l("Off-grid / unreliable"))],
        validators=[DataRequired()],
    )
    roof_type = SelectField(
        _l("Roof type"),
        choices=[
            ("", _l("Select roof type")),
            ("concrete-rcc", _l("Concrete (RCC)")),
            ("tin-metal", _l("Tin / Metal")),
            ("tiles", _l("Tiles")),
            ("asbestos", _l("Asbestos")),
            ("flat-roof", _l("Flat roof")),
            ("sloped-roof", _l("Sloped roof")),
            ("other", _l("Other")),
        ],
        validators=[Optional()],
    )
    submit = SubmitField(_l("Check eligibility & estimate"))


class TrackerEntryForm(FlaskForm):
    entry_type = SelectField(
        _l("Entry type"),
        choices=[
            ("generation", _l("Generation")),
            ("consumption", _l("Consumption")),
            ("export", _l("Export")),
            ("other", _l("Other")),
        ],
        validators=[DataRequired()],
    )
    kwh = DecimalField(_l("kWh"), validators=[DataRequired()], places=2, rounding=None)
    revenue = DecimalField(_l("Monetary value (₹)"), validators=[Optional()], places=2, rounding=None)
    panel_id = StringField(_l("Panel ID"), validators=[Optional(), Length(max=120)])
    date = DateField(_l("Entry date"), validators=[DataRequired()])
    note = TextAreaField(_l("Note"), validators=[Optional(), Length(max=500)])
    submit = SubmitField(_l("Save entry"))

