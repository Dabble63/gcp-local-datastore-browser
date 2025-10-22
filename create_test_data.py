#!/usr/bin/env python3
"""
Test data generator for Local Datastore Browser

This script creates sample entities in the datastore emulator for testing purposes.
Run this after starting the datastore emulator to populate it with test data.
"""

import os
import json
from datetime import datetime, timedelta
from google.cloud import datastore

def setup_environment():
    """Set up environment variables for datastore emulator"""
    os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:8081'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'

def create_client():
    """Create and return a datastore client"""
    return datastore.Client(project='test-project')

def create_users(client):
    """Create sample User entities"""
    print("Creating User entities...")
    
    users = [
        {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'age': 30,
            'active': True,
            'created_at': datetime.now() - timedelta(days=10),
            'preferences': {
                'theme': 'dark',
                'notifications': True,
                'language': 'en'
            },
            'tags': ['developer', 'python', 'flask']
        },
        {
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'age': 28,
            'active': True,
            'created_at': datetime.now() - timedelta(days=8),
            'preferences': {
                'theme': 'light',
                'notifications': False,
                'language': 'es'
            },
            'tags': ['designer', 'ui', 'ux']
        },
        {
            'name': 'Bob Johnson',
            'email': 'bob.johnson@example.com',
            'age': 35,
            'active': False,
            'created_at': datetime.now() - timedelta(days=5),
            'preferences': {
                'theme': 'auto',
                'notifications': True,
                'language': 'fr'
            },
            'tags': ['manager', 'team-lead']
        }
    ]
    
    for i, user_data in enumerate(users, 1):
        key = client.key('User', i)
        entity = datastore.Entity(key=key)
        entity.update(user_data)
        client.put(entity)
    
    print(f"✅ Created {len(users)} User entities")

def create_products(client):
    """Create sample Product entities"""
    print("Creating Product entities...")
    
    products = [
        {
            'name': 'Laptop Pro',
            'description': 'High-performance laptop for developers',
            'price': 1299.99,
            'category': 'Electronics',
            'in_stock': True,
            'quantity': 25,
            'created_at': datetime.now() - timedelta(days=30),
            'specifications': {
                'cpu': 'Intel i7',
                'ram': '16GB',
                'storage': '512GB SSD',
                'screen': '15.6 inch'
            },
            'ratings': [4.5, 4.8, 4.2, 4.9, 4.6]
        },
        {
            'name': 'Wireless Mouse',
            'description': 'Ergonomic wireless mouse with long battery life',
            'price': 29.99,
            'category': 'Accessories',
            'in_stock': True,
            'quantity': 150,
            'created_at': datetime.now() - timedelta(days=20),
            'specifications': {
                'connectivity': 'Bluetooth',
                'battery_life': '6 months',
                'dpi': '1600',
                'buttons': 3
            },
            'ratings': [4.1, 4.3, 4.0, 4.4]
        },
        {
            'name': 'Mechanical Keyboard',
            'description': 'RGB mechanical keyboard for gaming and typing',
            'price': 89.99,
            'category': 'Accessories',
            'in_stock': False,
            'quantity': 0,
            'created_at': datetime.now() - timedelta(days=15),
            'specifications': {
                'switch_type': 'Cherry MX Blue',
                'backlight': 'RGB',
                'layout': 'Full-size',
                'connectivity': 'USB-C'
            },
            'ratings': [4.7, 4.8, 4.9, 4.6, 4.8]
        }
    ]
    
    for product_data in products:
        # Use product name as string key for variety
        key = client.key('Product', product_data['name'].replace(' ', '_').lower())
        entity = datastore.Entity(key=key)
        entity.update(product_data)
        client.put(entity)
    
    print(f"✅ Created {len(products)} Product entities")

def create_orders(client):
    """Create sample Order entities"""
    print("Creating Order entities...")
    
    orders = [
        {
            'customer_email': 'john.doe@example.com',
            'total_amount': 1329.98,
            'status': 'completed',
            'order_date': datetime.now() - timedelta(days=3),
            'items': [
                {'product': 'Laptop Pro', 'quantity': 1, 'price': 1299.99},
                {'product': 'Wireless Mouse', 'quantity': 1, 'price': 29.99}
            ],
            'shipping_address': {
                'street': '123 Main St',
                'city': 'Anytown',
                'state': 'CA',
                'zipcode': '12345',
                'country': 'USA'
            },
            'payment_method': 'credit_card'
        },
        {
            'customer_email': 'jane.smith@example.com',
            'total_amount': 89.99,
            'status': 'pending',
            'order_date': datetime.now() - timedelta(days=1),
            'items': [
                {'product': 'Mechanical Keyboard', 'quantity': 1, 'price': 89.99}
            ],
            'shipping_address': {
                'street': '456 Oak Ave',
                'city': 'Another City',
                'state': 'NY',
                'zipcode': '67890',
                'country': 'USA'
            },
            'payment_method': 'paypal'
        }
    ]
    
    for i, order_data in enumerate(orders, 1001):
        key = client.key('Order', i)
        entity = datastore.Entity(key=key)
        entity.update(order_data)
        client.put(entity)
    
    print(f"✅ Created {len(orders)} Order entities")

def create_settings(client):
    """Create sample Settings entities"""
    print("Creating Settings entities...")
    
    settings = [
        {
            'key': 'app_name',
            'value': 'Local Datastore Browser',
            'type': 'string',
            'description': 'Application name displayed in the UI'
        },
        {
            'key': 'max_results_per_page',
            'value': 20,
            'type': 'integer',
            'description': 'Maximum number of results to show per page'
        },
        {
            'key': 'debug_mode',
            'value': True,
            'type': 'boolean',
            'description': 'Enable debug mode for development'
        },
        {
            'key': 'allowed_origins',
            'value': ['localhost:5000', '127.0.0.1:5000'],
            'type': 'array',
            'description': 'List of allowed origins for CORS'
        },
        {
            'key': 'database_config',
            'value': {
                'host': 'localhost',
                'port': 8081,
                'project': 'test-project',
                'timeout': 30
            },
            'type': 'object',
            'description': 'Database connection configuration'
        }
    ]
    
    for setting_data in settings:
        key = client.key('Settings', setting_data['key'])
        entity = datastore.Entity(key=key)
        entity.update(setting_data)
        client.put(entity)
    
    print(f"✅ Created {len(settings)} Settings entities")

def main():
    """Main function to create all test data"""
    print("🚀 Creating test data for Local Datastore Browser...")
    print("📍 Make sure the datastore emulator is running on localhost:8081")
    print("")
    
    # Setup environment
    setup_environment()
    
    try:
        # Create client
        client = create_client()
        
        # Test connection
        print("🔍 Testing connection to datastore emulator...")
        test_key = client.key('_test', 'connection')
        client.get(test_key)  # This will work even if entity doesn't exist
        print("✅ Connected to datastore emulator successfully!")
        print("")
        
        # Create test data
        create_users(client)
        create_products(client)
        create_orders(client)
        create_settings(client)
        
        print("")
        print("🎉 Test data created successfully!")
        print("")
        print("📊 Summary:")
        print("   • 3 User entities")
        print("   • 3 Product entities") 
        print("   • 2 Order entities")
        print("   • 5 Settings entities")
        print("")
        print("🌐 You can now browse the data at: http://localhost:5000")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        print("")
        print("💡 Make sure:")
        print("   • The datastore emulator is running")
        print("   • Environment variables are set correctly")
        print("   • Required Python packages are installed")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
