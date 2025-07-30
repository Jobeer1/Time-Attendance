#!/usr/bin/env python3
"""
Quick system validation test to ensure all components are working.
Tests Flask app creation and route registration.
"""

def test_flask_app():
    """Test Flask application creation and route registration"""
    print("Testing Flask Application Setup...")
    
    try:
        from app_new import app
        print("✓ Flask app imported successfully")
        
        # Test app configuration
        print(f"✓ Debug mode: {app.config.get('DEBUG', False)}")
        print(f"✓ Upload folder: {app.config.get('UPLOAD_FOLDER', 'uploads')}")
        
        # Test route registration
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append(f"{rule.methods} {rule.rule}")
        
        print(f"✓ Registered {len(routes)} routes:")
        for route in sorted(routes):
            print(f"  {route}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Test service imports and basic functionality"""
    print("\nTesting Service Imports...")
    
    try:
        from services.ocr_service import OCRService
        from services.pdf_service import PDFService
        from services.data_service import DataService
        from services.batch_service import BatchService
        
        print("✓ All services imported successfully")
        
        # Test OCR service basic functionality
        ocr_service = OCRService()
        print(f"✓ OCR service created with {len(ocr_service.table_configs)} configurations")
        
        # Test sample metadata extraction
        sample_text = "PROMED REP-SP0050X\nRUN DATE: 25.06.25\nDR. C.I. STOYANOV"
        metadata = ocr_service.extract_header_metadata(sample_text)
        print(f"✓ Metadata extraction working: {len(metadata)} items found")
        
        return True
        
    except Exception as e:
        print(f"✗ Service import error: {e}")
        return False

def test_configuration():
    """Test configuration setup"""
    print("\nTesting Configuration...")
    
    try:
        from config import Config
        
        print("✓ Configuration imported successfully")
        print(f"✓ Upload folder: {Config.UPLOAD_FOLDER}")
        print(f"✓ Output folder: {Config.OUTPUT_FOLDER}")
        print(f"✓ Supported PDF formats: {Config.SUPPORTED_PDF_FORMATS}")
        print(f"✓ Supported image formats: {Config.SUPPORTED_IMAGE_FORMATS}")
        
        # Test directory creation
        Config.ensure_directories_exist()
        print("✓ Directories created/verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("System Validation Tests")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_services, 
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All systems operational! Ready for PDF to CSV conversion.")
        print("\nTo start the application:")
        print("  python app_new.py")
        print("\nTo test OCR improvements:")
        print("  python test_ocr_improvements.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
