Accify Backend
Welcome to the Accify Backend project! This is a Django-based backend for a mobile application that supports:

User Authentication: Sign up, sign in, and sign out.
Contact Management: Users (e.g., drivers) can add trusted contacts.
Real-Time Tracking: Save and retrieve IoT-based location, speed, and accident data.
Accident Notification: Send notifications in real time to contacts and hospitals.
Dual Database Integration:
MySQL is used for relational data (accounts, contacts, IoT device metadata).
MongoDB is used for storing time-series location data.
The project uses Django REST Framework, djongo for MongoDB integration, and integrates with Firebase for notifications. It also includes a simulation script to emulate IoT device data.

Table of Contents
Features
Prerequisites
Installation & Setup
Configuration
Usage
Running the Server
Simulating IoT Data
Project Structure
Contributing
License
