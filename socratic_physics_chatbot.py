"""
Socratic Physics Chatbot with Interactive Simulations
Enhanced version with physics detection, simulations, and web interface
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import openai
import re
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string
import uuid

# Load environment variables
load_dotenv()

# Configuration
CSV_FILE = os.environ.get("CSV_FILE", "qa_pairs.csv")
TOP_K = int(os.environ.get("TOP_K", "3"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "deepseek-v4-pro")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.gapgpt.ir/v1")

# Cache paths
EMBEDDINGS_NPY = "qa_embeddings.npy"
METADATA_JSON = "qa_metadata.json"

# JEV Model Configuration
JEV_MODEL = "typesafe/jev-1.14"
JEV_API_URL = os.environ.get("JEV_API_URL", "https://api.gapgpt.ir/v1/systemone")

# Configure JEV API
JEV_API_KEY = os.environ.get("API_KEY")


# ============================================================================
# JEV MODEL FUNCTIONS
# ============================================================================

def call_jev_model(text, questions_config):
    """
    Call the typesafe/jev-1.14 model with structured questions.
    
    Args:
        text: The input text to analyze
        questions_config: Dictionary of questions to ask the model
    
    Returns:
        Dictionary with the model's responses
    """
    if not JEV_API_KEY:
        raise ValueError("JEV_API_KEY not configured")
    
    payload = {
        "model": JEV_MODEL,
        "state": {
            "text": text
        },
        "questions": questions_config
    }
    
    headers = {
        'Authorization': f'Bearer {JEV_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(JEV_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling JEV model: {e}")
        return None


# ============================================================================
# PHYSICS KEYWORDS FOR DETECTION
# ============================================================================

PHYSICS_KEYWORDS = [
    'physics', 'force', 'motion', 'velocity', 'acceleration', 'speed', 'momentum',
    'energy', 'work', 'power', 'gravity', 'mass', 'weight', 'friction', 'newton',
    'kinetic', 'potential', 'mechanics', 'dynamics', 'statics', 'projectile',
    'parabola', 'trajectory', 'bounce', 'collision', 'elastic', 'inelastic',
    'pendulum', 'oscillation', 'harmonic', 'wave', 'sound', 'light', 'optics',
    'electric', 'magnet', 'charge', 'current', 'voltage', 'resistance',
    'thermodynamics', 'heat', 'temperature', 'gas', 'pressure', 'fluid',
    'فیزیک', 'نیرو', 'حرکت', 'سرعت', 'شتاب', 'جرم', 'وزن', 'گرانش', 'انرژی',
    'کار', 'توان', 'تکانه', 'حرارت', 'دما', 'گاز', 'فشار', 'مکانیک'
]

# ============================================================================
# SIMULATION TEMPLATES
# ============================================================================

SIMULATION_TEMPLATES = {
    "ball_acceleration_velocity": """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Acceleration & Velocity</title>
<style>
body{margin:0;padding:20px;font-family:Arial,sans-serif;background:#f5f5f5}
.sim-container{background:white;border-radius:10px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
canvas{background:#222;border-radius:5px;display:block;margin:0 auto}
.controls{margin:15px 0;display:flex;gap:15px;flex-wrap:wrap}
.control-group{display:flex;flex-direction:column;gap:5px}
label{font-size:14px;font-weight:bold;color:#333}
input[type="range"]{width:200px}
.info{background:#e3f2fd;padding:10px;border-radius:5px;margin-top:10px;font-size:14px}
</style></head><body>
<div class="sim-container">
<h3 style="color:#333;text-align:center">Ball with Acceleration and Velocity</h3>
<p style="text-align:center;color:#666;font-size:14px">Object with acceleration but speed can be zero</p>
<canvas id="simCanvas" width="500" height="300"></canvas>
<div class="controls">
<div class="control-group">
<label for="velX">Velocity X: <span id="velXVal">2</span></label>
<input type="range" id="velX" min="-5" max="5" step="0.1" value="2">
</div>
<div class="control-group">
<label for="velY">Velocity Y: <span id="velYVal">3</span></label>
<input type="range" id="velY" min="-5" max="5" step="0.1" value="3">
</div>
<div class="control-group">
<label for="accX">Acceleration X: <span id="accXVal">-1</span></label>
<input type="range" id="accX" min="-5" max="5" step="0.1" value="-1">
</div>
<div class="control-group">
<label for="accY">Acceleration Y: <span id="accYVal">-0.5</span></label>
<input type="range" id="accY" min="-5" max="5" step="0.1" value="-0.5">
</div>
</div>
<div class="info">
<p><strong>Key Concept:</strong> At the highest point, vertical velocity is zero but acceleration (gravity) continues acting.</p>
</div>
</div>
<script>
const canvas=document.getElementById('simCanvas');
const ctx=canvas.getContext('2d');
const urlParams=new URLSearchParams(window.location.search);
let velX=parseFloat(urlParams.get('vx'))||2;
let velY=parseFloat(urlParams.get('vy'))||3;
let accX=parseFloat(urlParams.get('ax'))||-1;
let accY=parseFloat(urlParams.get('ay'))||-0.5;
document.getElementById('velX').value=velX;
document.getElementById('velY').value=velY;
document.getElementById('accX').value=accX;
document.getElementById('accY').value=accY;
document.getElementById('velXVal').textContent=velX;
document.getElementById('velYVal').textContent=velY;
document.getElementById('accXVal').textContent=accX;
document.getElementById('accYVal').textContent=accY;
let ball={x:250,y:150,radius:15};
let time=0;
let trail=[];
let maxTrail=100;

document.getElementById('velX').addEventListener('input',(e)=>{velX=parseFloat(e.target.value);document.getElementById('velXVal').textContent=velX;resetSim();});
document.getElementById('velY').addEventListener('input',(e)=>{velY=parseFloat(e.target.value);document.getElementById('velYVal').textContent=velY;resetSim();});
document.getElementById('accX').addEventListener('input',(e)=>{accX=parseFloat(e.target.value);document.getElementById('accXVal').textContent=accX;resetSim();});
document.getElementById('accY').addEventListener('input',(e)=>{accY=parseFloat(e.target.value);document.getElementById('accYVal').textContent=accY;resetSim();});

function resetSim(){ball.x=250;ball.y=150;time=0;trail=[];}

function update(){
time+=0.1;
const curVelX=velX+accX*time;
const curVelY=velY+accY*time;
ball.x+=curVelX*0.1;ball.y+=curVelY*0.1;
trail.push({x:ball.x,y:ball.y,vx:curVelX,vy:curVelY});
if(trail.length>maxTrail)trail.shift();
if(ball.x<ball.radius||ball.x>canvas.width-ball.radius||ball.y<ball.radius||ball.y>canvas.height-ball.radius)resetSim();
}

function draw(){
ctx.clearRect(0,0,canvas.width,canvas.height);
ctx.beginPath();
if(trail[0])ctx.moveTo(trail[0].x,trail[0].y);
for(let i=1;i<trail.length;i++)ctx.lineTo(trail[i].x,trail[i].y);
ctx.strokeStyle='rgba(255,255,255,0.3)';ctx.lineWidth=2;ctx.stroke();

ctx.beginPath();ctx.arc(ball.x,ball.y,ball.radius,0,Math.PI*2);ctx.fillStyle='#ff5722';ctx.fill();
ctx.strokeStyle='#ff9800';ctx.lineWidth=2;ctx.stroke();

const vScale=5;const curVelX=velX+accX*time;const curVelY=velY+accY*time;
ctx.beginPath();ctx.moveTo(ball.x,ball.y);ctx.lineTo(ball.x+curVelX*vScale,ball.y+curVelY*vScale);
ctx.strokeStyle='#4caf50';ctx.lineWidth=2;ctx.stroke();

const aScale=10;ctx.beginPath();ctx.moveTo(ball.x,ball.y);ctx.lineTo(ball.x+accX*aScale,ball.y+accY*aScale);
ctx.strokeStyle='#2196f3';ctx.lineWidth=2;ctx.stroke();

ctx.fillStyle='white';ctx.font='12px Arial';
ctx.fillText(`v=(${curVelX.toFixed(1)},${curVelY.toFixed(1)})`,10,20);
ctx.fillText(`a=(${accX},${accY})`,10,40);

const speed=Math.sqrt(curVelX*curVelX+curVelY*curVelY);
if(speed<0.5){ctx.fillStyle='#ffeb3b';ctx.font='bold 14px Arial';ctx.fillText('Velocity ≈ 0!',ball.x-60,ball.y-30);}
}

function animate(){update();draw();requestAnimationFrame(animate);}
animate();
canvas.addEventListener('click',()=>{resetSim();});
</script>
</body></html>
""",
    
    "projectile_motion": """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Projectile Motion</title>
<style>
body{margin:0;padding:20px;font-family:Arial,sans-serif;background:#f5f5f5}
.sim-container{background:white;border-radius:10px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
canvas{background:linear-gradient(to bottom,#1a237e,#3949ab);border-radius:5px;display:block;margin:0 auto}
.controls{margin:15px 0;display:flex;gap:15px;flex-wrap:wrap}
.control-group{display:flex;flex-direction:column;gap:5px}
label{font-size:14px;font-weight:bold;color:#333}
input[type="range"]{width:200px}
.info{background:#e3f2fd;padding:10px;border-radius:5px;margin-top:10px;font-size:14px}
</style></head><body>
<div class="sim-container">
<h3 style="color:#333;text-align:center">Projectile Motion</h3>
<p style="text-align:center;color:#666;font-size:14px">Parabolic trajectory under gravity</p>
<canvas id="simCanvas" width="600" height="400"></canvas>
<div class="controls">
<div class="control-group"><label for="angle">Angle: <span id="angleVal">45</span>°</label>
<input type="range" id="angle" min="0" max="90" step="1" value="45"></div>
<div class="control-group"><label for="speed">Speed: <span id="speedVal">15</span></label>
<input type="range" id="speed" min="5" max="30" step="1" value="15"></div>
<div class="control-group"><label for="gravity">Gravity: <span id="gravityVal">9.8</span></label>
<input type="range" id="gravity" min="0" max="20" step="0.1" value="9.8"></div>
</div>
<div class="info"><p><strong>Key:</strong> At peak, vertical velocity=0 but horizontal velocity constant. Gravity always downward.</p></div>
</div>
<script>
const canvas=document.getElementById('simCanvas');
const ctx=canvas.getContext('2d');
const urlParams=new URLSearchParams(window.location.search);
let angle=parseFloat(urlParams.get('angle'))||45;
let speed=parseFloat(urlParams.get('speed'))||15;
let gravity=parseFloat(urlParams.get('gravity'))||9.8;
document.getElementById('angle').value=angle;
document.getElementById('speed').value=speed;
document.getElementById('gravity').value=gravity;
document.getElementById('angleVal').textContent=angle;
document.getElementById('speedVal').textContent=speed;
document.getElementById('gravityVal').textContent=gravity;
let ball={x:50,y:canvas.height-50,radius:10};
let time=0;
let trail=[];
let maxTrail=200;
let isLaunched=false;

document.getElementById('angle').addEventListener('input',(e)=>{angle=parseFloat(e.target.value);document.getElementById('angleVal').textContent=angle;resetSim();});
document.getElementById('speed').addEventListener('input',(e)=>{speed=parseFloat(e.target.value);document.getElementById('speedVal').textContent=speed;resetSim();});
document.getElementById('gravity').addEventListener('input',(e)=>{gravity=parseFloat(e.target.value);document.getElementById('gravityVal').textContent=gravity;});

function resetSim(){ball.x=50;ball.y=canvas.height-50;time=0;trail=[];isLaunched=false;}
function launch(){isLaunched=true;time=0;trail=[];}

function update(){
if(!isLaunched)return;
time+=0.05;
const angleRad=angle*Math.PI/180;
const vx=speed*Math.cos(angleRad);
const vy=speed*Math.sin(angleRad)-gravity*time;
ball.x=50+vx*time*10;ball.y=canvas.height-50-(vy*time*10-0.5*gravity*(time*10)*(time*10));
trail.push({x:ball.x,y:ball.y,time:time});
if(trail.length>maxTrail)trail.shift();
if(ball.y>=canvas.height-50){isLaunched=false;ball.y=canvas.height-50;}
if(ball.x>canvas.width+ball.radius){isLaunched=false;resetSim();}
}

function draw(){
ctx.clearRect(0,0,canvas.width,canvas.height);
const gradient=ctx.createLinearGradient(0,0,0,canvas.height);
gradient.addColorStop(0,'#1a237e');gradient.addColorStop(1,'#3949ab');
ctx.fillStyle=gradient;ctx.fillRect(0,0,canvas.width,canvas.height);
ctx.fillStyle='#8d6e63';ctx.fillRect(0,canvas.height-30,canvas.width,30);

ctx.beginPath();
for(let i=0;i<trail.length;i++){if(i===0)ctx.moveTo(trail[i].x,trail[i].y);else ctx.lineTo(trail[i].x,trail[i].y);}
ctx.strokeStyle='rgba(255,255,255,0.5)';ctx.lineWidth=2;ctx.stroke();

ctx.beginPath();ctx.arc(ball.x,ball.y,ball.radius,0,Math.PI*2);ctx.fillStyle='#ff5722';ctx.fill();
ctx.strokeStyle='#ff9800';ctx.lineWidth=2;ctx.stroke();

const angleRad=angle*Math.PI/180;const vx=speed*Math.cos(angleRad);const vy=speed*Math.sin(angleRad)-gravity*time;
const vScale=3;ctx.beginPath();ctx.moveTo(ball.x,ball.y);ctx.lineTo(ball.x+vx*vScale,ball.y-vy*vScale);
ctx.strokeStyle='#4caf50';ctx.lineWidth=2;ctx.stroke();

ctx.beginPath();ctx.moveTo(ball.x,ball.y);ctx.lineTo(ball.x,ball.y+20);
ctx.strokeStyle='#2196f3';ctx.lineWidth=2;ctx.stroke();

ctx.fillStyle='white';ctx.font='12px Arial';
ctx.fillText(`vx=${(speed*Math.cos(angle*Math.PI/180)).toFixed(1)}`,10,20);
ctx.fillText(`vy=${(speed*Math.sin(angle*Math.PI/180)-gravity*time).toFixed(1)}`,10,40);

if(Math.abs(speed*Math.sin(angle*Math.PI/180)-gravity*time)<0.5){
ctx.fillStyle='#ffeb3b';ctx.font='bold 14px Arial';ctx.fillText('Peak: vy≈0!',ball.x-40,ball.y-25);
}

if(!isLaunched){
const launchX=50+speed*Math.cos(angle*Math.PI/180)*30;
const launchY=canvas.height-50-speed*Math.sin(angle*Math.PI/180)*30+0.5*gravity*30*30;
ctx.strokeStyle='rgba(255,255,255,0.3)';ctx.lineWidth=1;ctx.setLineDash([5,5]);
ctx.beginPath();ctx.moveTo(50,canvas.height-50);ctx.lineTo(launchX,launchY);ctx.stroke();ctx.setLineDash([]);
}
}

function animate(){update();draw();requestAnimationFrame(animate);}
animate();
canvas.addEventListener('click',()=>{if(!isLaunched)launch();});
</script>
</body></html>
""",
    
    "bouncing_ball": """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Bouncing Ball</title>
<style>
body{margin:0;padding:20px;font-family:Arial,sans-serif;background:#f5f5f5}
.sim-container{background:white;border-radius:10px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
canvas{background:#222;border-radius:5px;display:block;margin:0 auto}
.controls{margin:15px 0;display:flex;gap:15px;flex-wrap:wrap}
.control-group{display:flex;flex-direction:column;gap:5px}
label{font-size:14px;font-weight:bold;color:#333}
input[type="range"]{width:200px}
.info{background:#e3f2fd;padding:10px;border-radius:5px;margin-top:10px;font-size:14px}
</style></head><body>
<div class="sim-container">
<h3 style="color:#333;text-align:center">Bouncing Ball</h3>
<p style="text-align:center;color:#666;font-size:14px">Energy loss in collisions</p>
<canvas id="simCanvas" width="500" height="400"></canvas>
<div class="controls">
<div class="control-group"><label for="height">Height: <span id="heightVal">200</span></label>
<input type="range" id="height" min="50" max="350" step="10" value="200"></div>
<div class="control-group"><label for="restitution">Restitution: <span id="restitutionVal">0.8</span></label>
<input type="range" id="restitution" min="0" max="1" step="0.05" value="0.8"></div>
<div class="control-group"><label for="gravity">Gravity: <span id="gravityVal">0.5</span></label>
<input type="range" id="gravity" min="0.1" max="2" step="0.1" value="0.5"></div>
</div>
<div class="info"><p><strong>Key:</strong> Coefficient of restitution determines energy retained after bounce. 1=perfect, 0=stops.</p></div>
</div>
<script>
const canvas=document.getElementById('simCanvas');
const ctx=canvas.getContext('2d');
const urlParams=new URLSearchParams(window.location.search);
let height=parseFloat(urlParams.get('height'))||200;
let restitution=parseFloat(urlParams.get('restitution'))||0.8;
let gravity=parseFloat(urlParams.get('gravity'))||0.5;
document.getElementById('height').value=height;
document.getElementById('restitution').value=restitution;
document.getElementById('gravity').value=gravity;
document.getElementById('heightVal').textContent=height;
document.getElementById('restitutionVal').textContent=restitution;
document.getElementById('gravityVal').textContent=gravity;
let ball={x:250,y:20,radius:15,vy:0,vx:0};
let groundY=canvas.height-30;
let isDropped=false;
let bounceCount=0;
let trail=[];
let maxTrail=50;

document.getElementById('height').addEventListener('input',(e)=>{height=parseFloat(e.target.value);document.getElementById('heightVal').textContent=height;resetSim();});
document.getElementById('restitution').addEventListener('input',(e)=>{restitution=parseFloat(e.target.value);document.getElementById('restitutionVal').textContent=restitution;});
document.getElementById('gravity').addEventListener('input',(e)=>{gravity=parseFloat(e.target.value);document.getElementById('gravityVal').textContent=gravity;});

function resetSim(){ball.x=250;ball.y=20;ball.vy=0;ball.vx=0;isDropped=false;bounceCount=0;trail=[];}
function drop(){ball.y=height;ball.vy=0;isDropped=true;bounceCount=0;trail=[];}

function update(){
if(!isDropped)return;
ball.vy+=gravity;ball.y+=ball.vy;
trail.push({x:ball.x,y:ball.y,vy:ball.vy});
if(trail.length>maxTrail)trail.shift();
if(ball.y+ball.radius>groundY){ball.y=groundY-ball.radius;ball.vy=-ball.vy*restitution;bounceCount++;ball.vx=(Math.random()-0.5)*2;}
ball.vx*=0.98;ball.x+=ball.vx;
if(ball.x<ball.radius){ball.x=ball.radius;ball.vx=-ball.vx*0.5;}
else if(ball.x>canvas.width-ball.radius){ball.x=canvas.width-ball.radius;ball.vx=-ball.vx*0.5;}
if(Math.abs(ball.vy)<0.1&&Math.abs(ball.vx)<0.1&&ball.y>=groundY-ball.radius-1){isDropped=false;}
}

function draw(){
ctx.clearRect(0,0,canvas.width,canvas.height);
ctx.fillStyle='#8d6e63';ctx.fillRect(0,groundY,canvas.width,30);
ctx.beginPath();
for(let i=0;i<trail.length;i++){if(i===0)ctx.moveTo(trail[i].x,trail[i].y);else ctx.lineTo(trail[i].x,trail[i].y);}
ctx.strokeStyle='rgba(255,255,255,0.3)';ctx.lineWidth=1;ctx.stroke();

ctx.beginPath();ctx.arc(ball.x,ball.y,ball.radius,0,Math.PI*2);ctx.fillStyle='#ff5722';ctx.fill();
ctx.strokeStyle='#ff9800';ctx.lineWidth=2;ctx.stroke();

const vScale=3;ctx.beginPath();ctx.moveTo(ball.x,ball.y);ctx.lineTo(ball.x+ball.vx*vScale,ball.y+ball.vy*vScale);
ctx.strokeStyle='#4caf50';ctx.lineWidth=2;ctx.stroke();

ctx.beginPath();ctx.moveTo(ball.x,ball.y);ctx.lineTo(ball.x,ball.y+20);
ctx.strokeStyle='#2196f3';ctx.lineWidth=2;ctx.stroke();

ctx.fillStyle='white';ctx.font='12px Arial';
ctx.fillText(`vy=${ball.vy.toFixed(1)}`,10,20);ctx.fillText(`Bounces:${bounceCount}`,10,40);ctx.fillText(`Energy Loss:${((1-restitution)*100).toFixed(0)}%`,10,60);

if(Math.abs(ball.y-(groundY-ball.radius))<1&&Math.abs(ball.vy)>0.1){
ctx.fillStyle='#ffeb3b';ctx.font='bold 14px Arial';ctx.fillText('BOUNCE!',ball.x-30,ball.y-20);
}

if(!isDropped){ctx.strokeStyle='rgba(255,255,255,0.5)';ctx.lineWidth=1;ctx.setLineDash([5,5]);
ctx.beginPath();ctx.moveTo(250,height);ctx.lineTo(250,groundY);ctx.stroke();ctx.setLineDash([]);}
}

function animate(){update();draw();requestAnimationFrame(animate);}
animate();
canvas.addEventListener('click',()=>{if(!isDropped)drop();});
</script>
</body></html>
"""
}

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def load_csv_and_embeddings(client, filepath=CSV_FILE):
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: CSV file '{filepath}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    df.columns = [col.strip().lower() for col in df.columns]
    if "question" not in df.columns or "answer" not in df.columns:
        print("Error: CSV must contain 'question' and 'answer' columns.")
        sys.exit(1)

    df = df.dropna(subset=["question", "answer"])
    questions = df["question"].astype(str).str.strip().tolist()
    answers = df["answer"].astype(str).str.strip().tolist()

    if not questions:
        print("Error: CSV contains no valid Q&A pairs.")
        sys.exit(1)

    num_questions = len(questions)
    csv_mtime = os.path.getmtime(filepath)

    if os.path.exists(EMBEDDINGS_NPY) and os.path.exists(METADATA_JSON):
        try:
            with open(METADATA_JSON, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if (meta.get("csv_path") == os.path.abspath(filepath) and
                meta.get("csv_mtime") == csv_mtime and
                meta.get("num_questions") == num_questions):
                embeddings = np.load(EMBEDDINGS_NPY)
                if embeddings.shape[0] == num_questions:
                    print(f"Loaded {num_questions} embeddings from cache.")
                    return questions, answers, embeddings.tolist()
        except Exception as e:
            print(f"Cache loading failed ({e}), recomputing...")

    print(f"Loaded {num_questions} Q&A pairs. Computing embeddings...")
    try:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=questions)
        embeddings_list = [item.embedding for item in response.data]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        sys.exit(1)

    try:
        np.save(EMBEDDINGS_NPY, np.array(embeddings_list))
        metadata = {
            "csv_path": os.path.abspath(filepath),
            "csv_mtime": csv_mtime,
            "num_questions": num_questions
        }
        with open(METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print("Embeddings cached successfully.")
    except Exception as e:
        print(f"Warning: could not save cache ({e})")

    return questions, answers, embeddings_list


def retrieve_top_k(query, questions, answers, embeddings, client, k=TOP_K):
    if not embeddings:
        return []
    try:
        query_resp = client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
        query_emb = query_resp.data[0].embedding
    except Exception as e:
        print(f"Query embedding failed ({e})")
        return []
    
    sims = [cosine_similarity(query_emb, emb) for emb in embeddings]
    top_indices = np.argsort(sims)[-k:][::-1]
    results = []
    for idx in top_indices:
        if sims[idx] > 0:
            results.append((questions[idx], answers[idx]))
    return results


# ============================================================================
# PHYSICS DETECTION & EVALUATION
# ============================================================================

def is_physics_question(user_input, client=None):
    """
    Determine if a question is about physics using JEV model.
    Falls back to keyword matching if JEV is not available.
    """
    if not user_input or not user_input.strip():
        return False
    
    user_input_lower = user_input.lower()
    
    # Check for physics keywords (fast path)
    keyword_matches = sum(1 for kw in PHYSICS_KEYWORDS if kw.lower() in user_input_lower)
    
    if keyword_matches >= 2:
        return True
    
    # Use JEV model for classification
    try:
        questions_config = {
            "is_physics": {
                "type": "noul",
                "instructions": {
                    "question": "Is this a physics question?"
                }
            }
        }
        
        result = call_jev_model(user_input, questions_config)
        
        if result and "answers" in result:
            is_physics = result["answers"].get("is_physics", {}).get("answer", False)
            if is_physics:
                return True
    except Exception as e:
        print(f"JEV classification failed: {e}")
        pass
    
    # Fallback: Use LLM for classification if client available
    if client:
        try:
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "Classify if the following is a physics question. Respond only 'PHYSICS' or 'NOT_PHYSICS'."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.0,
                max_tokens=20
            )
            result = response.choices[0].message.content.strip().upper()
            return result == "PHYSICS"
        except:
            pass
    
    return keyword_matches >= 1



def _is_socratic_response(text):
    """
    Evaluate if a response is in Socratic style using JEV model.
    Falls back to pattern matching if JEV is not available.
    """
    if not text or not text.strip():
        return False
    
    text_lower = text.lower()
    
    # Check for refusal (fast path)
    if "متاسفم" in text and "فیزیک" in text:
        return True
    if "sorry" in text_lower and "physics" in text_lower:
        return True
    
    # Use JEV model for evaluation
    try:
        questions_config = {
            "is_socratic": {
                "type": "noul",
                "instructions": {
                    "question": "Is this a Socratic response (contains guiding questions, not direct answers)?"
                }
            },
            "has_questions": {
                "type": "noul",
                "instructions": {
                    "question": "Does the response contain multiple questions?"
                }
            },
            "has_direct_answer": {
                "type": "noul",
                "instructions": {
                    "question": "Does the response contain a direct answer or explanation?"
                }
            }
        }
        
        result = call_jev_model(text, questions_config)
        
        if result and "answers" in result:
            is_socratic = result["answers"].get("is_socratic", {}).get("answer", False)
            has_questions = result["answers"].get("has_questions", {}).get("answer", False)
            has_direct = result["answers"].get("has_direct_answer", {}).get("answer", False)
            
            # Must be socratic, have questions, and not have direct answers
            if is_socratic and has_questions and not has_direct:
                return True
            return False
    except Exception as e:
        print(f"JEV evaluation failed: {e}")
        pass
    
    # Fallback: Pattern matching
    # Count question marks
    question_count = text.count('?') + text.count('؟')
    
    if question_count >= 3:
        return True
    
    # Check for direct answer patterns
    direct_patterns = [
        'the answer is', 'the solution is', 'it is ', 'is equal to',
        'پاسخ این است', 'جواب این است', 'می باشد',
        'formula is', 'equation is'
    ]
    
    for pattern in direct_patterns:
        if pattern in text_lower:
            return False
    
    return question_count >= 2



# ============================================================================
# SIMULATION MATCHING
# ============================================================================

SIMULATION_TRIGGERS = {
    'acceleration': {
        'templates': ['ball_acceleration_velocity'],
        'keywords': ['acceleration', 'speed zero', 'velocity zero', 'deceleration', 'شتاب', 'سرعت صفر']
    },
    'projectile': {
        'templates': ['projectile_motion'],
        'keywords': ['projectile', 'parabola', 'trajectory', 'throw', 'launch', 'پرتاب', 'مسیر']
    },
    'bounce': {
        'templates': ['bouncing_ball'],
        'keywords': ['bounce', 'collision', 'elastic', 'inelastic', 'rebound', 'جستن', 'برخورد']
    },
    'newton': {
        'templates': ['ball_acceleration_velocity', 'projectile_motion', 'bouncing_ball'],
        'keywords': ['newton', 'law', 'force', 'نیرو', 'قانون نیوتن']
    },
    'energy': {
        'templates': ['bouncing_ball'],
        'keywords': ['energy', 'conservation', 'kinetic', 'potential', 'انرژی']
    }
}


def get_simulation_for_question(question):
    if not question:
        return []
    
    question_lower = question.lower()
    matched = []
    
    for category, config in SIMULATION_TRIGGERS.items():
        for keyword in config['keywords']:
            if keyword.lower() in question_lower:
                for template in config['templates']:
                    if template not in matched:
                        matched.append(template)
                break
    
    return matched


def generate_simulation_html(template_name, **params):
    if template_name in SIMULATION_TEMPLATES:
        return SIMULATION_TEMPLATES[template_name]
    return "<p>Simulation not available.</p>"


# ============================================================================
# WEB INTERFACE
# ============================================================================

app = Flask(__name__)
conversations = {}

CHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Socratic Physics Tutor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { color: #333; font-size: 24px; font-weight: 600; margin-bottom: 5px; }
        .header p { color: #666; font-size: 14px; }
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            margin: 20px auto;
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
        }
        .messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: rgba(255, 255, 255, 0.95);
        }
        .message { margin-bottom: 20px; display: flex; flex-direction: column; gap: 8px; }
        .message.user { align-items: flex-end; }
        .message.bot { align-items: flex-start; }
        .message-content {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 20px;
            line-height: 1.5;
            font-size: 15px;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        .message.bot .message-content {
            background: #f5f5f5;
            color: #333;
            border-bottom-left-radius: 5px;
        }
        .message-time { font-size: 11px; color: #999; padding: 0 10px; }
        .simulation-container {
            width: 100%;
            margin: 15px 0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .simulation-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            font-weight: 600;
            font-size: 14px;
        }
        .simulation-frame {
            width: 100%;
            height: 400px;
            border: none;
            background: white;
        }
        .input-container {
            padding: 20px;
            background: rgba(255, 255, 255, 0.95);
            border-top: 1px solid #eee;
        }
        .input-wrapper { display: flex; gap: 12px; align-items: flex-end; }
        .input-area {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 15px;
            resize: none;
            max-height: 100px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-area:focus { border-color: #667eea; }
        .send-button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .send-button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }
        .send-button:active { transform: translateY(0); }
        .send-button:disabled { opacity: 0.6; cursor: not-allowed; }
        .typing-indicator {
            display: none;
            padding: 10px 20px;
            background: #f5f5f5;
            border-radius: 20px;
            margin: 10px 0;
        }
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            margin: 0 3px;
            animation: bounce 1.4s infinite ease-in-out;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .info-bar {
            background: rgba(255, 255, 255, 0.9);
            padding: 10px 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #eee;
        }
        .welcome-message {
            text-align: center;
            padding: 30px 20px;
            color: #666;
            font-size: 16px;
            line-height: 1.6;
        }
        .welcome-message h2 { color: #333; margin-bottom: 10px; }
        @media (max-width: 768px) {
            .message-content { max-width: 90%; }
            .header h1 { font-size: 20px; }
            .chat-container { margin: 10px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Socratic Physics Tutor</h1>
        <p>Ask physics questions and learn through guided exploration</p>
    </div>
    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="welcome-message">
                <h2>Welcome to Physics Tutor</h2>
                <p>I'm your Socratic physics tutor. I won't give you direct answers, but I'll guide you through questions to help you understand physics concepts deeply.</p>
                <p>Try asking me about motion, forces, energy, or any physics topic!</p>
            </div>
        </div>
        <div class="typing-indicator" id="typingIndicator">
            <span></span><span></span><span></span>
        </div>
        <div class="input-container">
            <div class="input-wrapper">
                <textarea class="input-area" id="messageInput" placeholder="Ask a physics question..." rows="1"></textarea>
                <button class="send-button" id="sendButton">Send</button>
            </div>
        </div>
    </div>
    <div class="info-bar">
        Powered by AI | Physics questions only | Socratic method
    </div>
    <script>
        const messagesContainer = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        let conversationId = '{{ conversation_id }}';
        
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendButton.addEventListener('click', sendMessage);
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage('user', message);
            messageInput.value = '';
            messageInput.style.height = 'auto';
            typingIndicator.style.display = 'flex';
            sendButton.disabled = true;
            scrollToBottom();
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message, conversation_id: conversationId})
            })
            .then(response => response.json())
            .then(data => {
                typingIndicator.style.display = 'none';
                sendButton.disabled = false;
                addMessage('bot', data.response);
                if (data.simulation) {
                    addSimulation(data.simulation);
                }
                scrollToBottom();
            })
            .catch(error => {
                console.error('Error:', error);
                typingIndicator.style.display = 'none';
                sendButton.disabled = false;
                addMessage('bot', 'Sorry, an error occurred. Please try again.');
                scrollToBottom();
            });
        }
        
        function addMessage(type, content) {
            const welcomeMsg = document.querySelector('.welcome-message');
            if (welcomeMsg) welcomeMsg.remove();
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = content;
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString();
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
            messagesContainer.appendChild(messageDiv);
        }
        
        function addSimulation(html) {
            const simContainer = document.createElement('div');
            simContainer.className = 'simulation-container';
            const simHeader = document.createElement('div');
            simHeader.className = 'simulation-header';
            simHeader.textContent = 'Interactive Simulation';
            const simFrame = document.createElement('div');
            simFrame.className = 'simulation-frame';
            simFrame.innerHTML = html;
            simContainer.appendChild(simHeader);
            simContainer.appendChild(simFrame);
            messagesContainer.appendChild(simContainer);
        }
        
        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        scrollToBottom();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = []
    return render_template_string(CHAT_HTML, conversation_id=conversation_id)


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    conversation_id = data.get('conversation_id', str(uuid.uuid4()))
    
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    api_key = os.environ.get("API_KEY")
    if not api_key:
        return jsonify({'response': 'Error: API key not configured', 'simulation': None})
    
    client = openai.OpenAI(api_key=api_key, base_url=API_BASE_URL)
    
    questions, answers, embeddings = None, None, None
    if os.path.exists(CSV_FILE):
        try:
            questions, answers, embeddings = load_csv_and_embeddings(client, CSV_FILE)
        except Exception as e:
            print(f"Error loading data: {e}")
    
    if not is_physics_question(message, client):
        response = "متاسفم، من فقط به سوالات فیزیک پاسخ می دهم."
        return jsonify({'response': response, 'simulation': None})
    
    try:
        answer = get_socratic_response(message, client, questions, answers, embeddings, use_rag=questions is not None)
    except Exception as e:
        print(f"Error getting response: {e}")
        answer = "متاسفم، خطایی رخ داد. لطفا دوباره امتحان کنید."
    
    simulations = get_simulation_for_question(message)
    simulation_html = None
    if simulations:
        simulation_html = generate_simulation_html(simulations[0])
    
    conversations[conversation_id].append({'user': message, 'bot': answer, 'simulation': simulation_html})
    
    return jsonify({'response': answer, 'simulation': simulation_html})


def build_system_prompt(examples_text=""):
    base = """
You are a Socratic physics tutor. You help students learn physics through guided questions, not by giving direct answers.

Your role:
- You are a wise and patient teacher
- You guide students to discover answers through their own thinking
- You ask thought-provoking questions
- You never give direct answers or solutions
- You help students understand the underlying concepts

Guidelines:
1. Always ask questions, never state answers directly
2. Each response should contain 3-8 guiding questions
3. Ask questions that lead the student through the problem-solving process
4. From both the question and answer, extract concepts and ask about them
5. If the student asks a direct question, respond with questions that guide them
6. Never give formulas or equations directly
7. Always think step by step and ask questions at each step
8. For any physics problem, break it down into conceptual questions

Remember: "I cannot teach anybody anything. I can only make them think." - Socrates

Always respond in Persian for Persian questions, and in English for English questions.
"""
    
    if examples_text:
        base += "\n\nRelevant examples:\n" + examples_text
    
    return base


def format_examples(pairs):
    if not pairs:
        return ""
    text = ""
    for i, (q, a) in enumerate(pairs, start=1):
        text += f"\nExample {i}:\nQ: {q}\nA: {a}\n"
    return text


def get_socratic_response(user_input, client, questions=None, answers=None, embeddings=None, use_rag=True, top_k=TOP_K):
    if not is_physics_question(user_input, client):
        return "متاسفم، من فقط به سوالات فیزیک پاسخ می دهم."
    
    examples_text = ""
    if use_rag and questions and answers and embeddings is not None:
        pairs = retrieve_top_k(user_input, questions, answers, embeddings, client, k=top_k)
        examples_text = format_examples(pairs)
    
    system_prompt = build_system_prompt(examples_text)
    
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
    )
    
    answer = response.choices[0].message.content.strip()
    
    if not _is_socratic_response(answer):
        retry = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": answer},
                {"role": "user", "content": "Please rewrite with 4-8 guiding questions only, no statements."}
            ],
            temperature=0.5,
        )
        answer = retry.choices[0].message.content.strip()
    
    return answer


# ============================================================================
# MAIN
# ============================================================================

def run_web_server():
    print("Starting Socratic Physics Chatbot web server...")
    print("Open your browser and navigate to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)


def interactive_loop():
    api_key = os.environ.get("API_KEY")
    if not api_key:
        print("Error: Environment variable API_KEY is not set.")
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key, base_url=API_BASE_URL)
    questions, answers, embeddings = None, None, None
    if os.path.exists(CSV_FILE):
        questions, answers, embeddings = load_csv_and_embeddings(client, CSV_FILE)
    else:
        print("Warning: No QA pairs CSV found. Running without RAG.")

    print("Socratic Physics Tutor (type 'exit' or 'quit' to end)")
    print("-" * 50)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        
        if not user_input:
            continue

        simulations = get_simulation_for_question(user_input)
        answer = get_socratic_response(user_input, client, questions, answers, embeddings, use_rag=True)
        print("Tutor:", answer)
        
        if simulations:
            print(f"\n[SIMULATION AVAILABLE: {', '.join(simulations)}]")
            print("Run the web version to see interactive simulations!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Socratic Physics Chatbot')
    parser.add_argument('--web', action='store_true', help='Run web interface')
    parser.add_argument('--cli', action='store_true', help='Run CLI interface')
    args = parser.parse_args()
    
    if args.web:
        run_web_server()
    elif args.cli:
        interactive_loop()
    else:
        run_web_server()
