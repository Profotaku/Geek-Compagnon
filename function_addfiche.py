from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from dataclass import *
from config import *
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func