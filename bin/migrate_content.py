import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin
import sys

# Configuration
BASE_URL = "https://asroc.org.tw/"
PROJECT_ROOT = "/Users/salieri/code/ASROC/website/sources"
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "static/uploads")

# Paths for Chinese (zh-Hant)
NEWS_MD_PATH_ZH = os.path.join(PROJECT_ROOT, "content/news/index.zh-Hant.md")
MEETINGS_MD_PATH_ZH = os.path.join(PROJECT_ROOT, "content/meetings/_index.zh-Hant.md")
MINUTES_MD_PATH_ZH = os.path.join(PROJECT_ROOT, "content/about/minutes.zh-Hant.md")

# Paths for English (en)
NEWS_MD_PATH_EN = os.path.join(PROJECT_ROOT, "content/news/index.en.md")
MEETINGS_MD_PATH_EN = os.path.join(PROJECT_ROOT, "content/meetings/_index.en.md")
MINUTES_MD_PATH_EN = os.path.join(PROJECT_ROOT, "content/about/minutes.en.md")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def download_file(url, dest_path):
    if not url: return False
    full_url = urljoin(BASE_URL, url)
    if os.path.exists(dest_path):
        print(f"Skipping existing file: {dest_path}")
        return True
    try:
        print(f"Downloading {full_url}...")
        r = requests.get(full_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(r.content)
            print(f" -> Saved to {dest_path}")
            return True
        else:
            print(f"Failed to download {full_url}: Status {r.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {full_url}: {e}")
        return False

def parse_news(url, md_path, lang="zh"):
    print(f"Migrating News ({lang})...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Read frontmatter
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        frontmatter_match = re.match(r'^---(.*?)---\s*', existing_content, re.DOTALL)
        frontmatter = frontmatter_match.group(0) if frontmatter_match else "---\n---\n"
    else:
        # Create default frontmatter if file doesn't exist
        title = "News" if lang == "en" else "最新消息"
        frontmatter = f"---\ntitle: \"{title}\"\ndescription: \"All news\"\ncascade:\n  showDate: false\n  showAuthor: false\n  showSummary: true\n  invertPagination: true\n---\n"

    main_content = soup.find('td', {'valign': 'top'}) or soup.body
    text = main_content.get_text(separator='\n')
    lines = text.splitlines()
    new_entries = []
    
    current_date = None
    current_text = []
    date_pattern = re.compile(r'^\s*(\d{4}-\d{2}-\d{2})\s*$')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        date_match = date_pattern.match(line)
        if date_match:
            if current_date:
                full_text = " ".join(current_text)
                new_entries.append({'date': current_date, 'text': full_text})
            current_date = date_match.group(1)
            current_text = []
        else:
            if current_date: current_text.append(line)
    
    if current_date:
        full_text = " ".join(current_text)
        new_entries.append({'date': current_date, 'text': full_text})

    new_body = ""
    for entry in new_entries: 
        text_content = entry['text']
        url_match = re.search(r'(https?://[^\s]+)', text_content)
        if url_match:
            url = url_match.group(1)
            text_content = text_content.replace(url, f'[{{< icon "link" >}}]({url})')
        new_body += f"{{{{< badge >}}}} {entry['date']} {{{{< /badge >}}}}\n{text_content}\n\n"

    if new_body:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + "\n" + new_body)
        print(f"News ({lang}) updated.")

def parse_meetings(url, md_path, lang="zh"):
    print(f"Migrating Meetings ({lang})...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    tables = soup.find_all('table')
    target_table = None
    # Identify table by header keywords
    keyword = "Year" if lang == "en" else "年份"
    for tbl in tables:
        if keyword in tbl.get_text():
            target_table = tbl
            break
            
    if not target_table:
        print(f"Could not find meetings table for {lang}.")
        return

    markdown_rows = []
    trs = target_table.find_all('tr')
    
    for tr in trs:
        tds = tr.find_all('td')
        if not tds or len(tds) < 7: continue
            
        raw_year = tds[0].get_text(strip=True)
        # Clean year
        year = re.sub(r'[^\d]', '', raw_year) # Remove non-digits
        if not year: continue
        
        # Convert ROC year
        if len(year) <= 3:
            try: year_ad = str(int(year) + 1911)
            except: year_ad = year
        else: year_ad = year

        date_range = tds[1].get_text(strip=True)
        location = tds[2].get_text(strip=True)
        
        def process_asset(td_index, asset_name, icon_name):
            td = tds[td_index]
            link = td.find('a')
            if link:
                href = link.get('href')
                if not href: return ""
                ext = os.path.splitext(href)[1] or ".jpg"
                if "program" in asset_name: ext = ".pdf"
                
                filename = f"{asset_name}{ext}"
                local_rel_path = f"/website/uploads/meetings/{year_ad}/{filename}"
                local_abs_path = os.path.join(PROJECT_ROOT, f"static/uploads/meetings/{year_ad}/{filename}")
                download_file(href, local_abs_path)
                return f'[{{{{< icon "{icon_name}" >}}}}]({local_rel_path})'
            return ""

        album_td = tds[6]
        album_link = album_td.find('a')
        album_md = f'[{{{{< icon "images-regular" >}}}}]({album_link.get("href")})' if album_link else ""

        poster_md = process_asset(3, "poster", "image-regular")
        program_md = process_asset(4, "program", "calendar-regular")
        photo_md = process_asset(5, "group_photo", "camera-solid")
        
        row = f"| {year_ad} | {date_range} | {location} | {poster_md} | {program_md} | {photo_md} | {album_md} |"
        markdown_rows.append(row)

    # Headers
    if lang == "en":
        title = "Annual Meetings"
        table_header = "| Year | Date | Location | Poster | Program | Group Photo | Album |\n| --- | --- | --- | --- | --- | --- | --- |"
        frontmatter = f"---\ntitle: \"{title}\"\ndescription: \"Annual Meetings\"\nshowTableOfContents: false\ncascade:\n  showDate: false\n  showAuthor: false\n  showSummary: false\n  invertPagination: true\n---\n"
        map_html = '<div class="text-center">\n<iframe src="https://www.google.com/maps/d/u/1/embed?mid=1aNM2PmSlYGiuyS0Pykxket7P6DiPe7f1&ll=23.9843916564581%2C121&z=7"width="600" height="400"></iframe> \n</div>\n'
    else:
        # Keep existing frontmatter logic or read from file (simplified here for overwrite)
        title = "歷年年會"
        table_header = "| 年份 | 日期 | 地點 | 海報 | 議程 | 團體照 | 相本 |\n| --- | --- | --- | --- | --- | --- | --- |"
        frontmatter = f"---\ntitle: \"{title}\"\ndescription: \"歷年年會\"\nshowTableOfContents: false\ncascade:\n  showDate: false\n  showAuthor: false\n  showSummary: false\n  invertPagination: true\n---\n"
        map_html = '<div class="text-center">\n<iframe src="https://www.google.com/maps/d/u/1/embed?mid=1aNM2PmSlYGiuyS0Pykxket7P6DiPe7f1&ll=23.9843916564581%2C121&z=7"width="600" height="400"></iframe> \n</div>\n'

    content = f"{frontmatter}\n\n{map_html}\n{table_header}\n" + "\n".join(markdown_rows)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Meetings ({lang}) written to {md_path}")

def parse_minutes(url, md_path, lang="zh"):
    print(f"Migrating Minutes ({lang})...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    content_area = soup.find('td', {'valign': 'top'}) or soup.body
    links = content_area.find_all('a')
    
    sections = { "general": [], "council": [], "other": [] }
    last_year = None
    
    for link in links:
        href = link.get('href')
        text = link.get_text(strip=True)
        if not href: continue
        filename = os.path.basename(href)
        
        # Classification
        if filename.startswith("ASROC_"): section = "general"
        elif "minutes" in filename or "record" in filename: section = "council"
        else: continue

        display_date = text
        year_match = re.search(r'(\d{4})', text)
        if year_match: last_year = year_match.group(1)
        elif re.match(r'\d{2}-\d{2}', text) and last_year: display_date = f"{last_year}-{text}"
            
        save_year = last_year if last_year else "misc"
        local_rel_path = f"/website/uploads/minutes/{save_year}/{filename}"
        local_abs_path = os.path.join(PROJECT_ROOT, f"static/uploads/minutes/{save_year}/{filename}")
        download_file(href, local_abs_path)
        
        sections[section].append({ "date": display_date, "path": local_rel_path })

    # Move special cases to "other" (manual heuristic)
    # The heuristic in python script is hard. We will manually move 2009-02-28 if found in council
    # Actually, let's just dump.
    
    # Headers
    if lang == "en":
        title = "Minutes"
        desc = "Minutes of Meetings"
        h_general = "General Assembly"
        h_council = "Council Meeting"
        h_other = "Others"
        t_date = "Date"
        t_file = "File"
        dl_text = "Download PDF"
    else:
        title = "會議紀錄"
        desc = "歷年會議紀錄"
        h_general = "會員大會會議記錄 (General Assembly)"
        h_council = "理監事會議記錄 (Council Meeting)"
        h_other = "其他會議記錄 (Others)"
        t_date = "日期"
        t_file = "檔案"
        dl_text = "下載 PDF"

    md_content = f"---\ntitle: \"{title}\"\ndescription: \"{desc}\"\nmenu:\n  main:\n    parent: \"about\"\n---\n\n## {h_general}\n\n| {t_date} | {t_file} |\n| --- | --- |\n"
    for item in sections["general"]:
        md_content += f"| {item['date']} | [{dl_text}]({item['path']}) |\n"

    md_content += f"\n## {h_council}\n\n| {t_date} | {t_file} |\n| --- | --- |\n"
    for item in sections["council"]:
        # Manual fix for 2009-02-28
        if "2009-02-28" in item['date']: continue
        md_content += f"| {item['date']} | [{dl_text}]({item['path']}) |\n"

    md_content += f"\n## {h_other}\n\n| {t_date} | {t_file} |\n| --- | --- |\n"
    # Manual add for 2009-02-28 if it exists in council section
    found_other = False
    for item in sections["council"]:
        if "2009-02-28" in item['date']:
            md_content += f"| {item['date']} | [{dl_text}]({item['path']}) |\n"
            found_other = True
    
    # If not found there, maybe check logic. But for now, safe enough.
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Minutes ({lang}) written to {md_path}")

if __name__ == "__main__":
    # Chinese
    # parse_news(BASE_URL + "news.php", NEWS_MD_PATH_ZH, "zh")
    # parse_meetings(BASE_URL + "assembly.php", MEETINGS_MD_PATH_ZH, "zh")
    # parse_minutes(BASE_URL + "minutes.php", MINUTES_MD_PATH_ZH, "zh")
    
    # English
    parse_news(BASE_URL + "news_e.php", NEWS_MD_PATH_EN, "en")
    parse_meetings(BASE_URL + "assembly_e.php", MEETINGS_MD_PATH_EN, "en")
    parse_minutes(BASE_URL + "minutes_e.php", MINUTES_MD_PATH_EN, "en")
