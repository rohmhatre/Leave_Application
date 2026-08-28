#!/usr/bin/env python
"""Test PDF download functionality"""
import urllib.request
import http.cookiejar
import urllib.parse
import re

# Create a cookie jar and opener
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# First, fetch landing page to get CSRF token
landing_url = 'http://localhost:8000/'
try:
    response = opener.open(landing_url)
    html = response.read().decode('utf-8')
    # Extract CSRF token
    csrf_match = re.search(r'csrfmiddlewaretoken.*?value=["\']([^"\']+)["\']', html)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f'Got CSRF token: {csrf_token[:10]}...')
    else:
        print('⚠️  No CSRF token found, trying without it')
        csrf_token = ''
except Exception as e:
    print(f'Error fetching landing page: {e}')
    csrf_token = ''

# Login as student via landing page with CSRF token
login_url = 'http://localhost:8000/'
login_data = {
    'login_type': 'student',
    'roll_number': '25m0005',
    'password': 'testpass',
}
if csrf_token:
    login_data['csrfmiddlewaretoken'] = csrf_token

login_encoded = urllib.parse.urlencode(login_data).encode('utf-8')

try:
    response = opener.open(login_url, login_encoded)
    print(f'Login response: {response.status}')
    print(f'   Redirected to: {response.geturl()}')
    cookies = [c for c in cookie_jar]
    print(f'Session cookies: {len(cookies)} cookie(s)')
    for c in cookies:
        print(f'  - {c.name} = {c.value} (domain={c.domain})')
except Exception as e:
    print(f'Login error: {e}')

# Verify we can access home page
home_url = 'http://localhost:8000/home/'
try:
    response = opener.open(home_url)
    print(f'Home page accessible: {response.status}')
except Exception as e:
    print(f'❌ Home page error: {e}')

# Try to download PDF
pdf_url = 'http://localhost:8000/application/6/pdf/'
try:
    response = opener.open(pdf_url)
    content = response.read()
    
    print(f'\nPDF download response: {response.status}')
    print(f'Content-Type: {response.headers.get("Content-Type")}')
    print(f'URL: {response.geturl()}')
    print(f'PDF size: {len(content)} bytes')
    
    # Save to test file
    if response.status == 200 and len(content) > 1000:  # Actual PDF should be larger
        with open('test_pdf.pdf', 'wb') as f:
            f.write(content)
        print('PDF saved as test_pdf.pdf')
        # Verify PDF magic number
        if content[:4] == b'%PDF':
            print('✅ Valid PDF file (magic bytes confirmed)')
        else:
            print('⚠️  Content appears to be:', response.headers.get("Content-Type"))
    else:
        print(f'⚠️  Response size: {len(content)} bytes')
        if b'<!DOCTYPE' in content[:500]:
            print('⚠️  Response is HTML, not PDF')
            print('First 500 chars:', content[:500].decode('utf-8', errors='ignore'))
except Exception as e:
    print(f'❌ PDF download error: {e}')
