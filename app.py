from flask import Flask, render_template
import requests
import os
import base64

app = Flask(__name__)

def get_repo_structure(owner, repo, path=''):
    github_token = os.getenv('GITHUB_TOKEN')
    
    # Make sure we have a token
    if not github_token:
        print("Warning: GITHUB_TOKEN not set. Rate limits will be restricted.")
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Only add Authorization if we have a token
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            print(f"Repository or path {owner}/{repo}/{path} not found")
            return None
        elif response.status_code == 403:
            print("Rate limit exceeded. Please set GITHUB_TOKEN environment variable.")
            return None
        elif response.status_code != 200:
            print(f"Error fetching contents: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        contents = response.json()
        structure = []
        
        # Separate directories and files
        dirs = [item for item in contents if item['type'] == 'dir']
        files = [item for item in contents if item['type'] == 'file']
        
        # Sort directories and files alphabetically
        dirs.sort(key=lambda x: x['name'].lower())
        files.sort(key=lambda x: x['name'].lower())
        
        # Process files first, then directories
        for item in files:
            structure.append({
                'name': item['name'],
                'type': 'file',
                'path': item['path'],
                'url': item['html_url']
            })
            
        for item in dirs:
            subdir_contents = get_repo_structure(owner, repo, item['path'])
            structure.append({
                'name': item['name'],
                'type': 'dir',
                'path': item['path'],
                'contents': subdir_contents
            })
                
        return structure
        
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None

@app.route("/<owner>/<repo>")
def repo_structure(owner, repo):
    structure = get_repo_structure(owner, repo)
    if structure is None:
        return render_template("error.html", 
                             message="Repository not found or private, or rate limit exceeded!"), 404
    return render_template("index.html", structure=structure, repo=repo, owner=owner)

if __name__ == "__main__":
    # Only run in debug mode locally
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode)