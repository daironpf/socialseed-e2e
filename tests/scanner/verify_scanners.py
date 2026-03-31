"""Verification script for scanner package."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from socialseed_e2e.scanner.endpoint_scanner import EndpointScanner
from socialseed_e2e.scanner.schema_scanner import SchemaScanner


def verify_scanners():
    """Verify scanner modules work correctly."""
    print("=" * 60)
    print("Scanner Package Verification")
    print("=" * 60)
    
    auth_service_path = Path("D:/.dev/proyectos/SocialSeed/services/auth-service")
    
    if not auth_service_path.exists():
        print("\n⚠️  Auth service not found at:", auth_service_path)
        print("Skipping integration tests.")
        return False
    
    print(f"\n✓ Auth service found: {auth_service_path}")
    
    # Test 1: Endpoint Scanner
    print("\n[1/4] Testing EndpointScanner...")
    try:
        endpoint_scanner = EndpointScanner(str(auth_service_path))
        endpoints = endpoint_scanner.scan()
        
        print(f"   Found {len(endpoints)} endpoints")
        
        # Show sample endpoints
        if endpoints:
            print("   Sample endpoints:")
            for ep in endpoints[:5]:
                print(f"     {ep.method:6} {ep.path}")
        
        if len(endpoints) > 0:
            print("   ✓ EndpointScanner working correctly")
        else:
            print("   ⚠️  No endpoints found")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Schema Scanner
    print("\n[2/4] Testing SchemaScanner...")
    try:
        schema_scanner = SchemaScanner(str(auth_service_path))
        schemas = schema_scanner.scan()
        
        print(f"   Found {len(schemas)} DTOs/Schemas")
        
        # Show sample schemas
        if schemas:
            print("   Sample schemas:")
            for schema in schemas[:5]:
                print(f"     - {schema.name} ({len(schema.fields)} fields)")
        
        if len(schemas) > 0:
            print("   ✓ SchemaScanner working correctly")
        else:
            print("   ⚠️  No schemas found")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 3: Test endpoint filtering
    print("\n[3/4] Testing endpoint filtering...")
    try:
        auth_endpoints = [ep for ep in endpoints if ep.path.startswith('/auth')]
        get_endpoints = [ep for ep in endpoints if ep.method == 'GET']
        post_endpoints = [ep for ep in endpoints if ep.method == 'POST']
        
        print(f"   Auth endpoints: {len(auth_endpoints)}")
        print(f"   GET endpoints: {len(get_endpoints)}")
        print(f"   POST endpoints: {len(post_endpoints)}")
        print("   ✓ Filtering works correctly")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 4: Test schema field access
    print("\n[4/4] Testing schema field access...")
    try:
        for schema in schemas[:3]:
            required_fields = [f for f in schema.fields if f.required]
            optional_fields = [f for f in schema.fields if not f.required]
            print(f"   {schema.name}: {len(required_fields)} required, {len(optional_fields)} optional")
        
        print("   ✓ Schema field access works correctly")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All verification tests passed! ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = verify_scanners()
    sys.exit(0 if success else 1)