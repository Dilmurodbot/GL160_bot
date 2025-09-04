# Overview

This is a Telegram bot application built in Python that manages different user roles within a business context. The bot allows users to select from three distinct roles - Mijoz (Customer), Manager, and Investor - each with their own specific functionality and interface. The application uses role-based access control to provide customized experiences and features based on the user's selected role.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework Architecture
The application is built using the python-telegram-bot library with an async/await pattern for handling Telegram API interactions. The main entry point initializes a Telegram Application instance and registers command and callback query handlers for user interactions.

## Modular Handler System
The bot uses a separation of concerns approach with dedicated modules:
- **bot_handlers.py** - Contains the core message and button interaction handlers
- **keyboards.py** - Manages inline keyboard layouts for different user roles
- **user_roles.py** - Provides role management functionality and permission checking
- **config.py** - Centralizes configuration and role definitions

## Role-Based Access Control
The system implements a simple role-based permission system with three primary roles:
- **MIJOZ** (Customer) - Access to balance checking functionality
- **MANAGER** - Access to debt management features including Air and Container categories
- **INVESTOR** - Access to profit tracking features

## Role-Based User Assignment
User roles are assigned based on predefined user IDs in the config module:
- **Specific Manager ID**: 1454267949 - automatically assigned manager role
- **Specific Investor ID**: 2051160422 - automatically assigned investor role  
- **Default Mijoz Role**: All other user IDs automatically become customers (mijoz)

User roles are stored in a simple Python dictionary (USER_ROLES) within the config module for quick access during development.

## Event-Driven Interaction Model
The bot uses Telegram's callback query system to handle user interactions through inline keyboards. Each button press triggers specific handlers based on callback data patterns, enabling a conversational flow between different menu levels and role-specific features.

## Configuration Management
Application settings and role definitions are centralized in the config module, with environment variable support for sensitive data like bot tokens. This allows for easy deployment across different environments without code changes.

# External Dependencies

## Telegram Bot API
- **python-telegram-bot** library for Telegram API integration
- Handles webhook/polling for receiving updates
- Provides async support for message handling

## Environment Variables
- **BOT_TOKEN** - Required Telegram bot token from BotFather
- Retrieved through os.getenv() for secure token management

## Python Standard Library
- **asyncio** - For asynchronous operation handling
- **logging** - For application logging and debugging
- **os** - For environment variable access

Note: The current implementation uses in-memory storage for user roles. A production deployment would benefit from integrating a persistent database solution for user state management.