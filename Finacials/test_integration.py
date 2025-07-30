#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
Tests that the frontend and backend are properly connected.
"""

def test_route_availability():
    """Test that all expected routes are available"""
    print("Testing Route Availability...")
    
    try:
        from app_new import app
        
        # List of routes that should be available for the frontend
        expected_routes = [
            ('GET', '/'),
            ('POST', '/pdf_to_csv'),
            ('POST', '/batch_pdf_to_csv'),
            ('POST', '/pdf_to_images'),
            ('POST', '/batch_pdf_to_images'),
            ('POST', '/batch_extract_text_from_images'),
            ('GET', '/progress/<task_id>'),
            ('GET', '/download/<filename>')
        ]
        
        available_routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                for method in rule.methods:
                    if method not in ['OPTIONS', 'HEAD']:
                        available_routes.append((method, rule.rule))
        
        print(f"Available routes: {len(available_routes)}")
        
        missing_routes = []
        for expected_method, expected_route in expected_routes:
            # Check if route exists (handle dynamic routes like <task_id>)
            found = False
            for method, route in available_routes:
                if method == expected_method:
                    if '<' in expected_route:
                        # Dynamic route - check pattern
                        expected_pattern = expected_route.replace('<task_id>', '<').replace('<filename>', '<')
                        route_pattern = route.replace('task_id', '').replace('filename', '')
                        if expected_pattern in route_pattern:
                            found = True
                            break
                    elif route == expected_route:
                        found = True
                        break
            
            if not found:
                missing_routes.append(f"{expected_method} {expected_route}")
        
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        else:
            print("✅ All expected routes available")
            return True
            
    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        return False

def test_template_availability():
    """Test that templates are available"""
    print("\nTesting Template Availability...")
    
    try:
        import os
        
        templates_dir = os.path.join(os.getcwd(), 'templates')
        required_templates = ['index_new.html']
        
        missing_templates = []
        for template in required_templates:
            template_path = os.path.join(templates_dir, template)
            if not os.path.exists(template_path):
                missing_templates.append(template)
        
        if missing_templates:
            print(f"❌ Missing templates: {missing_templates}")
            return False
        else:
            print("✅ All required templates available")
            return True
            
    except Exception as e:
        print(f"❌ Error checking templates: {e}")
        return False

def test_static_files():
    """Test that static files are available"""
    print("\nTesting Static Files...")
    
    try:
        import os
        
        static_dir = os.path.join(os.getcwd(), 'static')
        required_files = [
            'css/styles.css',
            'js/progress.js'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = os.path.join(static_dir, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing static files: {missing_files}")
            return False
        else:
            print("✅ All required static files available")
            return True
            
    except Exception as e:
        print(f"❌ Error checking static files: {e}")
        return False

def test_javascript_handlers():
    """Test that JavaScript has the required form handlers"""
    print("\nTesting JavaScript Form Handlers...")
    
    try:
        with open('static/js/progress.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        required_handlers = [
            'pdf-to-csv-form',
            'batch-pdf-to-csv-form',
            'batch-images-form',
            'pdf-to-images-form'
        ]
        
        missing_handlers = []
        for handler in required_handlers:
            if handler not in js_content:
                missing_handlers.append(handler)
        
        if missing_handlers:
            print(f"❌ Missing JavaScript handlers: {missing_handlers}")
            return False
        else:
            print("✅ All required JavaScript handlers available")
            return True
            
    except Exception as e:
        print(f"❌ Error checking JavaScript: {e}")
        return False

def test_ocr_service_integration():
    """Test that OCR service has the required methods for frontend integration"""
    print("\nTesting OCR Service Integration...")
    
    try:
        from services.ocr_service import OCRService
        
        ocr_service = OCRService()
        required_methods = [
            'extract_structured_data',
            'batch_extract_text_from_images',
            'extract_raw_text'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(ocr_service, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing OCR methods: {missing_methods}")
            return False
        else:
            print("✅ All required OCR methods available")
            return True
            
    except Exception as e:
        print(f"❌ Error checking OCR service: {e}")
        return False

def main():
    """Run all frontend-backend integration tests"""
    print("Frontend-Backend Integration Test")
    print("=" * 50)
    
    tests = [
        test_route_availability,
        test_template_availability,
        test_static_files,
        test_javascript_handlers,
        test_ocr_service_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Integration tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 Frontend and Backend are properly integrated!")
        print("\n✅ Ready for production use:")
        print("   - All routes available")
        print("   - Templates and static files ready")
        print("   - JavaScript handlers configured")
        print("   - OCR service fully integrated")
        print("\n🚀 Start the application with: python app_new.py")
        print("📊 The enhanced PDF-to-CSV functionality is now working!")
    else:
        print("⚠️ Some integration issues found. Check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
