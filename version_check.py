#!/usr/bin/env python3

import requests
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

def check_pangolin_version():
    """Check the latest version of Pangolin software from official GitHub repo"""
    # Try the GitHub API first (most reliable)
    try:
        url = "https://api.github.com/repos/cov-lineages/pangolin/releases/latest"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        version = data["tag_name"]
        published_date = datetime.strptime(data["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        return {
            "version": version,
            "published_date": published_date,
            "url": data["html_url"]
        }
    except Exception as e:
        # If API fails, try parsing the HTML of the releases page
        try:
            url = "https://github.com/cov-lineages/pangolin/releases"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different selectors that might match release headers
            release_element = None
            selectors = [
                'div.release-header',  # Standard GitHub release header
                'div.release',         # Alternative release container
                'div.Box-row',         # Row in releases list
                'div[data-hovercard-type="release"]'  # Release with hovercard
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    release_element = elements[0]
                    break
            
            if not release_element:
                # If still not found, try the tags page
                url = "https://github.com/cov-lineages/pangolin/tags"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for tag information
                tag_element = soup.select_one('div.Box-row')
                if tag_element:
                    # Find the version/tag name
                    tag_link = tag_element.select_one('a[href*="/releases/tag/"]')
                    if tag_link:
                        version = tag_link.text.strip()
                        # Find the date if available
                        time_element = tag_element.select_one('relative-time')
                        if time_element and 'datetime' in time_element.attrs:
                            published_date = datetime.fromisoformat(time_element['datetime'].replace('Z', '+00:00')).strftime("%Y-%m-%d")
                        else:
                            published_date = "Unknown"
                            
                        return {
                            "version": version,
                            "published_date": published_date,
                            "url": f"https://github.com/cov-lineages/pangolin/releases/tag/{version}"
                        }
                
                # If still nothing, try a more aggressive tag search on tags page
                all_links = soup.find_all('a')
                version_links = [link for link in all_links if '/releases/tag/' in link.get('href', '') and 'v' in link.text]
                if version_links:
                    version = version_links[0].text.strip()
                    return {
                        "version": version,
                        "published_date": "Unknown",
                        "url": f"https://github.com/cov-lineages/pangolin/releases/tag/{version}"
                    }
                    
                return {"error": f"Could not find Pangolin version information"}
            
            # Extract version from the first release/tag found
            version_tag = None
            # Try different version tag selectors
            for selector in ['a.Link--primary', 'a[href*="/releases/tag/"]', 'a[data-hovercard-type="release"]']:
                version_tag = release_element.select_one(selector)
                if version_tag:
                    break
                    
            if not version_tag:
                return {"error": "Could not find version tag"}
            
            version = version_tag.text.strip()
            
            # Extract date
            time_tag = release_element.select_one('relative-time')
            if time_tag and 'datetime' in time_tag.attrs:
                published_date = datetime.fromisoformat(time_tag['datetime'].replace('Z', '+00:00')).strftime("%Y-%m-%d")
            else:
                published_date = "Unknown"
            
            return {
                "version": version,
                "published_date": published_date,
                "url": f"https://github.com/cov-lineages/pangolin/releases/tag/{version}"
            }
        except Exception as nested_e:
            return {"error": f"Failed to retrieve Pangolin version: {str(e)}, then {str(nested_e)}"}

def check_artic_version():
    """Check the latest version of ARTIC field bioinformatics pipeline from GitHub"""
    try:
        url = "https://api.github.com/repos/artic-network/fieldbioinformatics/releases/latest"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        version = data["tag_name"]
        published_date = datetime.strptime(data["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        return {
            "version": version,
            "published_date": published_date,
            "url": data["html_url"]
        }
    except Exception as e:
        return {"error": f"Failed to retrieve ARTIC version: {str(e)}"}

def check_artic_sarscov2_primers():
    """Check the latest SARS-CoV-2 primer versions from ARTIC GitHub"""
    try:
        # First, we'll get the HTML content from the GitHub page since the API doesn't show all folders
        url = "https://github.com/artic-network/primer-schemes/tree/master/sars-cov-2"
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML to find directories
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all rows in the file browser
        rows = soup.find_all('div', class_='Box-row')
        
        # Extract directory names (looking for version patterns like V1, V2, etc.)
        versions = []
        for row in rows:
            # Look for directory icons followed by version-like names
            if row.find('svg', class_='octicon-file-directory-fill'):
                name_element = row.find('a', class_='js-navigation-open')
                if name_element:
                    name = name_element.text.strip()
                    # Check if it looks like a version number
                    if re.match(r'V?\d+(\.\d+)*', name, re.IGNORECASE):
                        versions.append(name)
        
        # If no versions found with regex, try to get all directory names
        if not versions:
            versions = [row.find('a', class_='js-navigation-open').text.strip() 
                      for row in rows 
                      if row.find('svg', class_='octicon-file-directory-fill') 
                      and row.find('a', class_='js-navigation-open')]
        
        # Sort versions - handle both V5.3 and 5.3 format
        versions.sort(key=lambda x: [float(n) if n.replace('.', '', 1).isdigit() else 0 
                                    for n in re.findall(r'\d+\.\d+|\d+', x)], 
                     reverse=True)
        
        if not versions:
            return {"error": "No primer versions found"}
            
        latest_version = versions[0]
        
        return {
            "latest_version": latest_version,
            "all_versions": versions,
            "url": f"https://github.com/artic-network/primer-schemes/tree/master/sars-cov-2/{latest_version}"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve ARTIC SARS-CoV-2 primers: {str(e)}"}

def check_artic_ncov2019_primers():
    """Check all available SARS-CoV-2 primer versions from ARTIC GitHub"""
    try:
        # Get the HTML content from the GitHub page
        url = "https://github.com/artic-network/primer-schemes/tree/master/nCoV-2019"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all directory items - looking for specific GitHub UI elements
        versions = []
        
        # Find all links that might be directories
        for a_tag in soup.find_all('a'):
            # Check if this is a directory link in the file browser
            if a_tag.has_attr('href') and '/tree/master/nCoV-2019/' in a_tag['href'] and a_tag.text.strip():
                dir_name = a_tag.text.strip()
                # Skip parent directories or non-version directories
                if dir_name != '..' and dir_name != '.' and dir_name != 'nCoV-2019':
                    versions.append(dir_name)
        
        # Remove duplicates while preserving order
        seen = set()
        versions = [x for x in versions if not (x in seen or seen.add(x))]
        
        # If we still don't have versions, try an alternative approach
        if not versions:
            # Look for rows in file browser that contain directories
            for row in soup.find_all('div', role='row'):
                # Check if this row has an SVG icon for directory
                svg_icon = row.find('svg', class_='octicon-file-directory-fill')
                if svg_icon:
                    # Get the name from the link in this row
                    name_link = row.find('a')
                    if name_link and name_link.text.strip():
                        versions.append(name_link.text.strip())
        
        # If we still have nothing, try a more general approach
        if not versions:
            for row in soup.find_all('div', class_=['Box-row', 'js-navigation-item']):
                if row.find('svg', class_=['octicon-file-directory-fill', 'directory']):
                    name_link = row.find('a')
                    if name_link:
                        name = name_link.text.strip()
                        versions.append(name)
        
        if not versions:
            return {"error": "Could not detect ARTIC primer versions from the GitHub page"}
            
        # Sort versions to get latest first - handle V1, V2, V3.1, etc.
        try:
            # Sort by numeric value - handle V prefix if present
            versions.sort(key=lambda x: [float(n) if n.replace('.', '', 1).isdigit() else 0 
                                       for n in re.findall(r'\d+\.\d+|\d+', x)], 
                         reverse=True)
        except:
            # If sorting fails, just return them as is
            pass
        
        return {
            "all_versions": versions,
            "url": url
        }
    except Exception as e:
        return {"error": f"Failed to retrieve ARTIC nCoV-2019 primers: {str(e)}"}

def main():
    """Main function to check and display version information"""
    print("=" * 60)
    print("CHECKING LATEST VERSIONS OF SARS-CoV-2 TOOLS")
    print("=" * 60)
    
    # Check Pangolin
    print("\n1. Pangolin Repository")
    print("-" * 60)
    pangolin_info = check_pangolin_version()
    if "error" in pangolin_info:
        print(f"  {pangolin_info['error']}")
    else:
        print(f"  Latest version: {pangolin_info['version']}")
        print(f"  Published date: {pangolin_info['published_date']}")
        print(f"  URL: {pangolin_info['url']}")
    
    # Check ARTIC
    print("\n2. ARTIC Field Bioinformatics")
    print("-" * 60)
    artic_info = check_artic_version()
    if "error" in artic_info:
        print(f"  {artic_info['error']}")
    else:
        print(f"  Latest version: {artic_info['version']}")
        print(f"  Published date: {artic_info['published_date']}")
        print(f"  URL: {artic_info['url']}")
    
    # Check ARTIC SARS-CoV-2 primer schemes
    print("\n3. ARTIC nCoV-2019 Primer Schemes")
    print("-" * 60)
    schemes_info = check_artic_ncov2019_primers()
    if "error" in schemes_info:
        print(f"  {schemes_info['error']}")
    else:
        print(f"  Available primer versions:")
        if 'all_versions' in schemes_info and schemes_info['all_versions']:
            for version in schemes_info['all_versions']:
                print(f"    - {version}")
        print(f"  URL: {schemes_info['url']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
