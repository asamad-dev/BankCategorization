#!/usr/bin/env python3
"""
Setup script for Veryfi Bank Statement Processing
Helps users configure their environment and test the integration
"""
import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version OK: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        os.system("pip install -r requirements.txt")
        print("✅ Dependencies installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_veryfi_import():
    """Test if veryfi can be imported"""
    try:
        import veryfi
        print("✅ Veryfi library imported successfully")
        return True
    except ImportError:
        print("❌ Veryfi library not available")
        print("Run: pip install veryfi")
        return False

def setup_environment_variables():
    """Help user set up environment variables"""
    print("\n🔧 Setting up Veryfi API credentials...")
    print("You need to get your API credentials from: https://www.veryfi.com/")
    print("\nRequired environment variables:")
    print("- VERYFI_CLIENT_ID")
    print("- VERYFI_CLIENT_SECRET")
    print("- VERYFI_USERNAME")
    print("- VERYFI_API_KEY")
    
    # Check if already set
    env_vars = {
        'VERYFI_CLIENT_ID': os.getenv('VERYFI_CLIENT_ID'),
        'VERYFI_CLIENT_SECRET': os.getenv('VERYFI_CLIENT_SECRET'),
        'VERYFI_USERNAME': os.getenv('VERYFI_USERNAME'),
        'VERYFI_API_KEY': os.getenv('VERYFI_API_KEY')
    }
    
    all_set = all(env_vars.values())
    
    if all_set:
        print("✅ All environment variables are set!")
        return True
    else:
        print("\n❌ Missing environment variables:")
        for key, value in env_vars.items():
            if not value:
                print(f"  - {key}")
        
        print("\n📝 To set environment variables:")
        print("Windows Command Prompt:")
        print("  set VERYFI_CLIENT_ID=your_client_id")
        print("  set VERYFI_CLIENT_SECRET=your_client_secret")
        print("  set VERYFI_USERNAME=your_username")
        print("  set VERYFI_API_KEY=your_api_key")
        
        print("\nWindows PowerShell:")
        print("  $env:VERYFI_CLIENT_ID='your_client_id'")
        print("  $env:VERYFI_CLIENT_SECRET='your_client_secret'")
        print("  $env:VERYFI_USERNAME='your_username'")
        print("  $env:VERYFI_API_KEY='your_api_key'")
        
        print("\nLinux/Mac:")
        print("  export VERYFI_CLIENT_ID=your_client_id")
        print("  export VERYFI_CLIENT_SECRET=your_client_secret")
        print("  export VERYFI_USERNAME=your_username")
        print("  export VERYFI_API_KEY=your_api_key")
        
        print("\nAlternatively, create a .env file:")
        print("  1. Copy env.example to .env:")
        print("     cp env.example .env")
        print("  2. Edit .env with your actual credentials")
        print("  3. The script will automatically load them")
        
        return False

def test_configuration():
    """Test the Veryfi configuration"""
    print("\n🧪 Testing Veryfi configuration...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from Preprocess.PreprocressCommon import VeryfiConfig
        
        config = VeryfiConfig()
        if config.is_configured():
            print("✅ Veryfi configuration is valid!")
            return True
        else:
            print("❌ Veryfi configuration incomplete")
            return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def create_output_directories():
    """Create necessary output directories"""
    print("\n📁 Creating output directories...")
    directories = [
        "output",
        "output/processed_statements"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")

def show_usage_example():
    """Show usage example"""
    print("\n📖 Usage Example:")
    print("="*50)
    print("# 1. Run the bank statement processor:")
    print("python src/Preprocess/PreprocressBankStatement.py")
    print()
    print("# 2. Or use it programmatically:")
    print("from src.Preprocess.PreprocressBankStatement import BankStatementProcessor")
    print("from src.Preprocess.PreprocressCommon import VeryfiConfig")
    print()
    print("config = VeryfiConfig()")
    print("processor = BankStatementProcessor(config)")
    print("result = processor.process_bank_statement('path/to/statement.pdf')")
    print("processor.export_to_csv('output.csv')")
    print()
    print("Your Wells Fargo statement will be processed automatically!")

def main():
    """Main setup function"""
    print("🏦 Bank Statement Processing with Veryfi - Setup Script")
    print("="*60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Check veryfi import
    if not check_veryfi_import():
        success = False
    
    # Setup environment variables
    if not setup_environment_variables():
        success = False
    
    # Test configuration
    if success and not test_configuration():
        success = False
    
    # Create directories
    create_output_directories()
    
    # Show results
    print("\n" + "="*60)
    if success:
        print("🎉 Setup completed successfully!")
        show_usage_example()
    else:
        print("⚠️  Setup completed with issues. Please resolve the above problems.")
        print("\nNext steps:")
        print("1. Get Veryfi API credentials from: https://www.veryfi.com/")
        print("2. Set environment variables as shown above")
        print("3. Re-run this setup script")
    
    return success

if __name__ == "__main__":
    main()
