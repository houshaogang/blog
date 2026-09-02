const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Config
const ARTICLE_DATE = '2026-09-02';
const POSTS_DIR = 'D:/blog/content/posts';
const ENV_FILE = 'D:/blog/scripts/.env';
const TITLE = '80后90后的失眠：我们为什么越长大越睡不着';
const DIGEST = '小时候倒头就睡，长大后却在深夜睁着眼。你的失眠，不是你的错，是这个时代给认真生活的人留下的后遗症。';

// Read .env
function readEnv(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const env = {};
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
      const eqIdx = trimmed.indexOf('=');
      env[trimmed.substring(0, eqIdx).trim()] = trimmed.substring(eqIdx + 1).trim();
    }
  }
  return env;
}

// Simple HTTP GET
function httpGet(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const req = client.get(url, { timeout: 120000 }, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        return httpGet(res.headers.location).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => resolve(Buffer.concat(chunks)));
      res.on('error', reject);
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

// Simple HTTP POST JSON
function httpPostJson(url, data) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const postData = JSON.stringify(data);
    const options = {
      hostname: parsed.hostname,
      port: parsed.port || 443,
      path: parsed.pathname + parsed.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
      },
    };
    const client = url.startsWith('https') ? https : http;
    const req = client.request(options, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        try {
          resolve(JSON.parse(Buffer.concat(chunks).toString()));
        } catch (e) {
          reject(new Error('Invalid JSON: ' + Buffer.concat(chunks).toString()));
        }
      });
      res.on('error', reject);
    });
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

// Simple HTTP GET returning JSON
function httpGetJson(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const req = client.get(url, { timeout: 30000 }, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        try {
          resolve(JSON.parse(Buffer.concat(chunks).toString()));
        } catch (e) {
          reject(new Error('Invalid JSON: ' + Buffer.concat(chunks).toString()));
        }
      });
      res.on('error', reject);
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

// HTTP GET returning buffer (for image download)
function httpGetBuffer(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const req = client.get(url, { timeout: 120000 }, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        return httpGetBuffer(res.headers.location).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        reject(new Error('HTTP ' + res.statusCode));
        return;
      }
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => resolve(Buffer.concat(chunks)));
      res.on('error', reject);
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

// Multipart upload
function multipartUpload(url, filePath, fieldName) {
  return new Promise((resolve, reject) => {
    const fileBuffer = fs.readFileSync(filePath);
    const filename = path.basename(filePath);
    const boundary = '----FormBoundary' + Date.now().toString(36);
    
    let body = '';
    body += '--' + boundary + '\r\n';
    body += 'Content-Disposition: form-data; name="' + fieldName + '"; filename="' + filename + '"\r\n';
    body += 'Content-Type: image/png\r\n\r\n';
    
    const bodyStart = Buffer.from(body, 'utf8');
    const bodyEnd = Buffer.from('\r\n--' + boundary + '--\r\n', 'utf8');
    const fullBody = Buffer.concat([bodyStart, fileBuffer, bodyEnd]);
    
    const parsed = new URL(url);
    const options = {
      hostname: parsed.hostname,
      port: parsed.port || 443,
      path: parsed.pathname + parsed.search,
      method: 'POST',
      headers: {
        'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'Content-Length': fullBody.length,
      },
    };
    
    const client = url.startsWith('https') ? https : http;
    const req = client.request(options, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        try {
          resolve(JSON.parse(Buffer.concat(chunks).toString()));
        } catch (e) {
          reject(new Error('Invalid JSON: ' + Buffer.concat(chunks).toString()));
        }
      });
      res.on('error', reject);
    });
    req.on('error', reject);
    req.write(fullBody);
    req.end();
  });
}

// Markdown to HTML conversion
function markdownToHtml(md) {
  let lines = md.split('\n');
  let html = '';
  
  for (let i = 0; i < lines.length; i++) {
    let trimmed = lines[i].trim();
    
    // Empty line
    if (trimmed === '') {
      continue;
    }
    
    // HR
    if (trimmed === '---') {
      html += '<hr style="border:none;border-top:1px solid #ddd;margin:30px 0;" />\n';
      continue;
    }
    
    // H1
    if (trimmed.startsWith('# ') && !trimmed.startsWith('## ')) {
      const text = trimmed.substring(2);
      html += '<h1 style="font-size:24px;font-weight:bold;color:#333;margin:0 0 20px 0;text-align:center;">' + inlineStyle(text) + '</h1>\n';
      continue;
    }
    
    // H2
    if (trimmed.startsWith('## ')) {
      const text = trimmed.substring(3);
      html += '<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 15px 0;border-left:4px solid #c0392b;padding-left:12px;">' + inlineStyle(text) + '</h2>\n';
      continue;
    }
    
    // Center italic text (wrapped in *...* on its own line, not bold **)
    if (trimmed.startsWith('*') && trimmed.endsWith('*') && !trimmed.startsWith('**')) {
      const text = trimmed.slice(1, -1);
      html += '<p style="text-align:center;font-size:15px;color:#888;margin:20px 0;font-style:italic;">' + text + '</p>\n';
      continue;
    }
    
    // Regular paragraph
    html += '<p style="margin-bottom:15px;font-size:16px;line-height:1.8;color:#333;">' + inlineStyle(trimmed) + '</p>\n';
  }
  
  return html;
}

function inlineStyle(text) {
  // Bold: **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight:bold;color:#222;">$1</strong>');
  // Italic: *text* (but not ** already handled)
  text = text.replace(/\*([^*]+?)\*/g, '<em style="font-style:italic;color:#666;">$1</em>');
  return text;
}

// Count Chinese characters + words
function countWords(text) {
  const chinese = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const english = (text.match(/[a-zA-Z]+/g) || []).length;
  return chinese + english;
}

async function main() {
  try {
    // 1. Read env
    console.log('=== Step 1: Reading .env ===');
    const env = readEnv(ENV_FILE);
    const appId = env.WEIXIN_APP_ID;
    const appSecret = env.WEIXIN_APP_SECRET;
    console.log('APP_ID:', appId);
    console.log('APP_SECRET:', appSecret.substring(0, 6) + '***');

    // 2. Check for existing cover image
    console.log('\n=== Step 2: Checking for cover image ===');
    const coverPath = path.join(POSTS_DIR, 'cover_' + ARTICLE_DATE + '.png');
    let useCoverPath = coverPath;
    
    if (fs.existsSync(coverPath)) {
      console.log('Found today\'s cover:', coverPath);
    } else {
      // Find latest cover
      const files = fs.readdirSync(POSTS_DIR)
        .filter(f => f.startsWith('cover_') && (f.endsWith('.png') || f.endsWith('.jpg')))
        .sort()
        .reverse();
      if (files.length > 0) {
        useCoverPath = path.join(POSTS_DIR, files[0]);
        console.log('Using latest cover:', useCoverPath);
      } else {
        console.log('No existing cover found, will download new one...');
        const prompt = encodeURIComponent('warm nostalgic night scene street light dreamy healing watercolor painting style');
        const seed = Math.floor(Math.random() * 100000);
        const imageUrl = 'https://image.pollinations.ai/prompt/' + prompt + '?width=900&height=383&nologo=true&seed=' + seed;
        console.log('Downloading cover from:', imageUrl);
        const imgBuffer = await httpGetBuffer(imageUrl);
        fs.writeFileSync(coverPath, imgBuffer);
        useCoverPath = coverPath;
        console.log('Cover saved to:', coverPath);
      }
    }

    // 3. Read article and convert to HTML
    console.log('\n=== Step 3: Converting markdown to HTML ===');
    const mdContent = fs.readFileSync(path.join(POSTS_DIR, ARTICLE_DATE + '-insomnia-8090.md'), 'utf8');
    let htmlContent = markdownToHtml(mdContent);
    
    // Add footer
    htmlContent += '\n<hr style="border:none;border-top:1px solid #ddd;margin:40px 0 20px 0;" />\n';
    htmlContent += '<p style="text-align:center;font-size:14px;color:#999;margin:10px 0;">深夜解忧铺</p>\n';
    htmlContent += '<p style="text-align:center;font-size:14px;color:#999;margin:10px 0;">你的心事，有人听。</p>\n';
    
    console.log('HTML length:', htmlContent.length, 'chars');
    
    // Count words
    const wordCount = countWords(mdContent);
    console.log('Article word count:', wordCount);

    // Save HTML for reference
    fs.writeFileSync(path.join(POSTS_DIR, ARTICLE_DATE + '-insomnia-8090.html'), htmlContent);
    console.log('HTML saved for reference');

    // 4. Get access token
    console.log('\n=== Step 4: Getting access token ===');
    const tokenUrl = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=' + appId + '&secret=' + appSecret;
    const tokenResult = await httpGetJson(tokenUrl);
    if (tokenResult.errcode) {
      console.error('Token error:', tokenResult);
      process.exit(1);
    }
    const accessToken = tokenResult.access_token;
    console.log('Access token obtained:', accessToken.substring(0, 20) + '...');

    // 5. Upload cover image
    console.log('\n=== Step 5: Uploading cover image ===');
    const uploadUrl = 'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=' + accessToken + '&type=image';
    console.log('Uploading:', useCoverPath);
    const uploadResult = await multipartUpload(uploadUrl, useCoverPath, 'media');
    console.log('Upload result:', JSON.stringify(uploadResult));
    if (uploadResult.errcode) {
      console.error('Upload error:', uploadResult);
      process.exit(1);
    }
    const thumbMediaId = uploadResult.media_id;
    console.log('thumb_media_id:', thumbMediaId);

    // 6. Create draft
    console.log('\n=== Step 6: Creating draft ===');
    const draftUrl = 'https://api.weixin.qq.com/cgi-bin/draft/add?access_token=' + accessToken;
    const draftData = {
      articles: [{
        title: TITLE,
        digest: DIGEST,
        content: htmlContent,
        thumb_media_id: thumbMediaId,
        need_open_comment: 1,
        only_fans_can_comment: 0,
      }]
    };
    const draftResult = await httpPostJson(draftUrl, draftData);
    console.log('Draft result:', JSON.stringify(draftResult));
    if (draftResult.errcode) {
      console.error('Draft error:', draftResult);
      process.exit(1);
    }
    const mediaId = draftResult.media_id;
    console.log('Draft media_id:', mediaId);

    // 7. Verify
    console.log('\n=== Step 7: Verifying draft ===');
    const verifyUrl = 'https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=' + accessToken;
    const verifyResult = await httpPostJson(verifyUrl, { offset: 0, count: 1 });
    console.log('Verify result:', JSON.stringify(verifyResult, null, 2));
    
    if (verifyResult.item && verifyResult.item.length > 0) {
      const firstDraft = verifyResult.item[0];
      const draftTitle = firstDraft.content && firstDraft.content.news_item && firstDraft.content.news_item[0] 
        ? firstDraft.content.news_item[0].title 
        : 'N/A';
      console.log('\n=== VERIFICATION ===');
      console.log('Latest draft title:', draftTitle);
      console.log('Title contains Chinese:', /[\u4e00-\u9fff]/.test(draftTitle));
    }

    // Summary
    console.log('\n=== SUMMARY ===');
    console.log('Article Title:', TITLE);
    console.log('Word Count:', wordCount);
    console.log('Draft media_id:', mediaId);
    console.log('Cover used:', useCoverPath);
    console.log('Verification: Draft created successfully');

  } catch (err) {
    console.error('Error:', err.message);
    console.error(err.stack);
    process.exit(1);
  }
}

main();
