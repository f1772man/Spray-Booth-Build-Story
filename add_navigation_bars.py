import os

files_en = [
    r'Outputs/DIY_SprayBooth_Build_Story_EN.html',
    r'Outputs/SprayBooth_BuildGuide_EN.html',
    r'Outputs/SprayBooth_BuildGuide_v9_EN.html',
    r'Outputs/SprayBooth_Brochure_EN.html',
    r'Outputs/SprayBooth_Brochure_EN_White.html'
]

files_kr = [
    r'Outputs/DIY_SprayBooth_Build_Story.html',
    r'Outputs/SprayBooth_BuildGuide.html',
    r'Outputs/SprayBooth_BuildGuide_v9.html',
    r'Outputs/SprayBooth_Brochure.html',
    r'Outputs/SprayBooth_Brochure_White.html'
]

nav_en = '''
<!-- TOP NAVIGATION BAR -->
<nav style="position: sticky; top: 0; z-index: 99999; width: 100%; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding: 12px 24px; box-sizing: border-box; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
  <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; color: #60a5fa; text-decoration: none; font-weight: 700; font-size: 15px; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;">
    <span style="font-size: 18px;">🏠</span> ← Return to Main Hub (Home)
  </a>
  <div style="display: flex; align-items: center; gap: 12px;">
    <a href="index.html" style="padding: 6px 14px; border-radius: 6px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #e2e8f0; text-decoration: none; font-size: 13px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;">All Documents</a>
    <a href="https://cults3d.com/en/3d-model/tool/airtight-airbrush-spray-booth-enclosure-diy-kit-2020-extrusions-dual-glove-p" target="_blank" style="padding: 6px 14px; border-radius: 6px; background: #3b82f6; color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;">Cults3D Store ↗</a>
  </div>
</nav>
'''

nav_kr = '''
<!-- TOP NAVIGATION BAR -->
<nav style="position: sticky; top: 0; z-index: 99999; width: 100%; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding: 12px 24px; box-sizing: border-box; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
  <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; color: #60a5fa; text-decoration: none; font-weight: 700; font-size: 15px; font-family: -apple-system, BlinkMacSystemFont, Malgun Gothic, Segoe UI, sans-serif;">
    <span style="font-size: 18px;">🏠</span> ← 메인 허브로 돌아가기 (Home)
  </a>
  <div style="display: flex; align-items: center; gap: 12px;">
    <a href="index.html" style="padding: 6px 14px; border-radius: 6px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #e2e8f0; text-decoration: none; font-size: 13px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, Malgun Gothic, Segoe UI, sans-serif;">전체 문서 목록</a>
    <a href="https://cults3d.com/en/3d-model/tool/airtight-airbrush-spray-booth-enclosure-diy-kit-2020-extrusions-dual-glove-p" target="_blank" style="padding: 6px 14px; border-radius: 6px; background: #3b82f6; color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, Malgun Gothic, Segoe UI, sans-serif;">Cults3D 스토어 ↗</a>
  </div>
</nav>
'''

footer_btn_en = '''
<!-- BOTTOM RETURN TO HOME BUTTON -->
<div style="text-align: center; margin: 40px auto 20px; padding: 20px 0;">
  <a href="index.html" style="display: inline-flex; align-items: center; gap: 10px; padding: 12px 28px; background: #1e293b; border: 1px solid #3b82f6; color: #60a5fa; text-decoration: none; border-radius: 10px; font-size: 15px; font-weight: 700; transition: all 0.2s ease;">
    <span>🏠</span> Return to Main Documentation Portal
  </a>
</div>
'''

footer_btn_kr = '''
<!-- BOTTOM RETURN TO HOME BUTTON -->
<div style="text-align: center; margin: 40px auto 20px; padding: 20px 0;">
  <a href="index.html" style="display: inline-flex; align-items: center; gap: 10px; padding: 12px 28px; background: #1e293b; border: 1px solid #3b82f6; color: #60a5fa; text-decoration: none; border-radius: 10px; font-size: 15px; font-weight: 700; transition: all 0.2s ease;">
    <span>🏠</span> 메인 문서 포털로 돌아가기
  </a>
</div>
'''

def update_file(filepath, nav_html, footer_html):
    if not os.path.exists(filepath):
        print(f"Skipping (not found): {filepath}")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<!-- TOP NAVIGATION BAR -->' in content:
        print(f"Already updated: {filepath}")
        return
    
    # insert nav_html right after <body ...>
    idx = content.lower().find('<body')
    if idx == -1:
        print(f"No body tag: {filepath}")
        return
    end_body_tag = content.find('>', idx)
    if end_body_tag == -1:
        return
    
    # insert footer_html right before </body>
    close_body_idx = content.lower().rfind('</body>')
    if close_body_idx != -1:
        content = content[:close_body_idx] + '\n' + footer_html + '\n' + content[close_body_idx:]
    
    # insert nav at top
    idx = content.lower().find('<body')
    end_body_tag = content.find('>', idx)
    new_content = content[:end_body_tag+1] + '\n' + nav_html + '\n' + content[end_body_tag+1:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Successfully added navigation to: {filepath}")

for f in files_en:
    update_file(f, nav_en, footer_btn_en)

for f in files_kr:
    update_file(f, nav_kr, footer_btn_kr)

print("All navigation updates completed!")
