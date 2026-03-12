// ===== DOM Elements =====
const apiKeyInput = document.getElementById('apiKeyInput');
const topicInput = document.getElementById('topicInput');
const languageGroup = document.getElementById('languageGroup');
const languageSelect = document.getElementById('languageSelect');
const generateBtn = document.getElementById('generateBtn');
const landingState = document.getElementById('landingState');
const resultsState = document.getElementById('resultsState');
const topicTag = document.getElementById('topicTag');
const langTag = document.getElementById('langTag');
const newBlogBtn = document.getElementById('newBlogBtn');
const blogContent = document.getElementById('blogContent');
const pipelineNodes = document.getElementById('pipelineNodes');
const reviewScore = document.getElementById('reviewScore');
const reviewFeedback = document.getElementById('reviewFeedback');
const wordCount = document.getElementById('wordCount');
const sectionCount = document.getElementById('sectionCount');
const reviewCount = document.getElementById('reviewCount');
const copyBtn = document.getElementById('copyBtn');

// ===== Pipeline Node Definitions =====
const PIPELINE_NODES = [
    { id: 'outline_generation', label: 'Outline' },
    { id: 'title_creation', label: 'Title' },
    { id: 'intro_generation', label: 'Introduction' },
    { id: 'section_generation', label: 'Sections' },
    { id: 'takeaways_cta', label: 'Takeaways & CTA' },
    { id: 'review', label: 'Review' },
];

let currentBlog = null;
let nodeTimestamps = {};

// ===== Show language dropdown when topic is typed =====
topicInput.addEventListener('input', () => {
    const hasTopic = topicInput.value.trim().length > 0;
    languageGroup.classList.toggle('hidden', !hasTopic);
    generateBtn.disabled = !hasTopic;
});

// ===== Generate Blog =====
generateBtn.addEventListener('click', startGeneration);

async function startGeneration() {
    const topic = topicInput.value.trim();
    const language = languageSelect.value;
    const apiKey = apiKeyInput.value.trim();

    if (!topic) return;
    if (!apiKey) {
        apiKeyInput.style.borderColor = '#f43f5e';
        apiKeyInput.focus();
        setTimeout(() => apiKeyInput.style.borderColor = '', 2000);
        return;
    }

    // Switch to results state
    landingState.classList.add('hidden');
    resultsState.classList.remove('hidden');

    // Set top bar tags
    topicTag.textContent = topic;
    langTag.textContent = language || 'English';

    // Initialize pipeline nodes
    const nodes = language
        ? [...PIPELINE_NODES, { id: 'translation', label: 'Translation' }]
        : PIPELINE_NODES;
    initPipelineUI(nodes);

    // Reset stats
    blogContent.innerHTML = '<div class="skeleton" style="width:80%"></div><div class="skeleton" style="width:60%"></div><div class="skeleton" style="width:90%"></div><div class="skeleton" style="width:70%"></div>';
    reviewScore.textContent = '--';
    reviewFeedback.textContent = '';
    wordCount.textContent = '--';
    sectionCount.textContent = '--';
    reviewCount.textContent = '--';

    // Start SSE stream
    nodeTimestamps = { start: Date.now() };
    await streamBlog(topic, language, apiKey, nodes);
}

// ===== Initialize Pipeline UI =====
function initPipelineUI(nodes) {
    pipelineNodes.innerHTML = nodes.map(node => `
        <div class="pipeline-node pending" data-node="${node.id}">
            <div class="node-dot"></div>
            <span class="node-name">${node.label}</span>
            <span class="node-time"></span>
        </div>
    `).join('');
}

// ===== Update Pipeline Node Status =====
function updateNodeStatus(nodeId, status, duration) {
    const nodeEl = document.querySelector(`[data-node="${nodeId}"]`);
    if (!nodeEl) return;

    nodeEl.className = `pipeline-node ${status}`;

    if (status === 'completed' && duration !== undefined) {
        nodeEl.querySelector('.node-time').textContent = `${duration}s`;
    }

    if (status === 'completed') {
        nodeEl.querySelector('.node-dot').textContent = '✓';
    }
}

// ===== Stream Blog via SSE =====
async function streamBlog(topic, language, apiKey, nodes) {
    try {
        const response = await fetch('/blogs/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                language: language,
                api_key: apiKey,
            }),
        });

        if (!response.ok) {
            const err = await response.json();
            blogContent.innerHTML = `<p style="color: #f43f5e;">Error: ${err.detail || 'Generation failed'}</p>`;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let lastNodeId = null;
        let lastNodeTime = Date.now();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete data in buffer

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.replace('data: ', '');

                try {
                    const data = JSON.parse(jsonStr);
                    handleSSEEvent(data, nodes, lastNodeId, lastNodeTime);

                    // Track timing
                    if (data.node !== 'complete') {
                        // Mark previous node completed
                        if (lastNodeId) {
                            const duration = ((Date.now() - lastNodeTime) / 1000).toFixed(1);
                            updateNodeStatus(lastNodeId, 'completed', duration);
                        }
                        // Mark current node active
                        updateNodeStatus(data.node, 'active');
                        lastNodeId = data.node;
                        lastNodeTime = Date.now();
                    } else {
                        // Complete: mark last node done
                        if (lastNodeId) {
                            const duration = ((Date.now() - lastNodeTime) / 1000).toFixed(1);
                            updateNodeStatus(lastNodeId, 'completed', duration);
                        }
                    }
                } catch (e) {
                    console.error('SSE parse error:', e);
                }
            }
        }
    } catch (error) {
        blogContent.innerHTML = `<p style="color: #f43f5e;">Connection error: ${error.message}</p>`;
    }
}

// ===== Handle SSE Event =====
function handleSSEEvent(data) {
    if (data.node === 'complete') return;

    // Update blog content if available
    if (data.blog) {
        currentBlog = data.blog;
        renderBlog(data.blog);
    }

    // Update review info
    if (data.review_score !== undefined) {
        reviewScore.textContent = data.review_score;
        reviewScore.style.color = data.review_score >= 7 ? '#10b981' : '#f59e0b';
        reviewFeedback.textContent = data.review_feedback || '';
        reviewCount.textContent = data.review_count || 0;
    }

    // Update translated content
    if (data.translated_content) {
        blogContent.innerHTML = `<div class="translated-blog">${marked.parse(data.translated_content)}</div>`;
    }
}

// ===== Render Blog =====
function renderBlog(blog) {
    let html = '';

    if (blog.title) {
        html += `<h1>${blog.title}</h1>`;
    }
    if (blog.meta_description) {
        html += `<p class="meta-desc">${blog.meta_description}</p>`;
    }
    if (blog.introduction) {
        html += `<p>${blog.introduction}</p>`;
    }

    if (blog.sections && blog.sections.length > 0) {
        blog.sections.forEach(section => {
            html += `<h2>${section.heading}</h2>`;
            html += `<p>${section.content}</p>`;
        });
    }

    if (blog.key_takeaways && blog.key_takeaways.length > 0) {
        html += `<div class="takeaways"><h3>📌 Key Takeaways</h3><ul>`;
        blog.key_takeaways.forEach(t => html += `<li>${t}</li>`);
        html += `</ul></div>`;
    }

    if (blog.call_to_action) {
        html += `<div class="cta">💡 ${blog.call_to_action}</div>`;
    }

    blogContent.innerHTML = html;

    // Update stats
    const totalWords = [blog.introduction, ...blog.sections.map(s => s.content)].join(' ').split(/\s+/).length;
    wordCount.textContent = totalWords.toLocaleString();
    sectionCount.textContent = blog.sections.length;
}

// ===== Copy Blog =====
copyBtn.addEventListener('click', () => {
    if (!currentBlog) return;

    let text = `# ${currentBlog.title}\n\n`;
    text += `${currentBlog.introduction}\n\n`;
    currentBlog.sections.forEach(s => {
        text += `## ${s.heading}\n\n${s.content}\n\n`;
    });
    text += `## Key Takeaways\n\n`;
    currentBlog.key_takeaways.forEach(t => text += `- ${t}\n`);
    text += `\n${currentBlog.call_to_action}`;

    navigator.clipboard.writeText(text).then(() => {
        copyBtn.textContent = '✅ Copied!';
        setTimeout(() => copyBtn.textContent = '📋 Copy', 2000);
    });
});

// ===== New Blog Button =====
newBlogBtn.addEventListener('click', () => {
    resultsState.classList.add('hidden');
    landingState.classList.remove('hidden');
    topicInput.value = '';
    languageSelect.value = '';
    languageGroup.classList.add('hidden');
    generateBtn.disabled = true;
    currentBlog = null;
});