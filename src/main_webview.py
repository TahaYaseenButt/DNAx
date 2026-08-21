import os
import sys

# Ensure src/ is in sys.path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import webview
from api_bridge import ApiBridge

def get_entry_url():
    """Locates the React production build index.html either from source or PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    html_path = os.path.join(base_path, 'ui', 'dist', 'index.html')
    
    # Return as file URL
    if os.path.exists(html_path):
        normalized = html_path.replace('\\', '/')
        if not normalized.startswith('/'):
            return f"file:///{normalized}"
        return f"file://{normalized}"
    
    return html_path

def main():
    api = ApiBridge()
    entry_url = get_entry_url()

    # Create native Windows WebView2 desktop window with React UI
    window = webview.create_window(
        title='DNAx Laboratory Suite v2.0 PRO',
        url=entry_url,
        js_api=api,
        width=1280,
        height=840,
        min_size=(960, 640),
        background_color='#020617',
        text_select=True,
    )

    is_frozen = getattr(sys, 'frozen', False)
    webview.start(debug=not is_frozen, http_server=True)

if __name__ == '__main__':
    main()
