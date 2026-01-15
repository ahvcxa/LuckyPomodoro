"""
Gelişmiş Multiplayer Pomodoro Uygulaması
FastAPI + WebSockets ile gerçek zamanlı senkronize Pomodoro sayacı
Target Timestamp mantığı ile doğru zamanlama
Leaderboard ve Adil Puanlama Sistemi Eklendi
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import uuid
import asyncio
import logging
import os
from pathlib import Path

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI uygulaması
app = FastAPI(title="Multiplayer Pomodoro 🍀")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates klasörü
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Templates klasörünü kontrol et ve oluştur
if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR.mkdir(exist_ok=True)
    logger.warning(f"Templates klasörü bulunamadı, oluşturuldu: {TEMPLATES_DIR}")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Static dosyalar için
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Varsayılan Pomodoro ayarları (saniye cinsinden)
DEFAULT_WORK_DURATION = 25 * 60      # 25 dakika
DEFAULT_SHORT_BREAK = 5 * 60         # 5 dakika
DEFAULT_LONG_BREAK = 15 * 60         # 15 dakika


class ConnectionManager:
    """
    WebSocket bağlantılarını ve oda durumlarını yöneten sınıf.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[WebSocket, dict]] = {}
        self.room_states: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_name: str):
        """Kullanıcıyı bir odaya bağlar"""
        # Oda yoksa oluştur
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            self.room_states[room_id] = {
                "timer": {
                    "remaining_seconds": DEFAULT_WORK_DURATION,
                    "is_running": False,
                    "target_timestamp": None,
                    "mode": "work"
                },
                "settings": {
                    "work_duration": DEFAULT_WORK_DURATION,
                    "short_break": DEFAULT_SHORT_BREAK,
                    "long_break": DEFAULT_LONG_BREAK
                },
                "users": []
            }
        
        # Şimdiki zamanı al (UTC)
        now = datetime.now(timezone.utc)
        
        # Kullanıcı bilgisini oluştur (RANK SİSTEMİ İÇİN GÜNCELLENDİ)
        user_info = {
            "name": user_name,
            "id": str(uuid.uuid4()),
            "joined_at": now.isoformat(),
            "total_seconds": 0,  # <--- Toplam puan (saniye cinsinden)
            # Eğer o sırada timer çalışıyorsa, başlangıç zamanını "şimdi" yap (Geç gelen için)
            # Çalışmıyorsa None yap
            "current_session_start": now.isoformat() if self.room_states[room_id]["timer"]["is_running"] else None
        }
        
        self.active_connections[room_id][websocket] = user_info
        
        # Kullanıcı listesine ekle (id kontrolü ile)
        existing_user = next(
            (u for u in self.room_states[room_id]["users"] if u["id"] == user_info["id"]),
            None
        )
        if not existing_user:
            self.room_states[room_id]["users"].append(user_info)
        
        logger.info(f"Kullanıcı '{user_name}' '{room_id}' odasına katıldı")
        
        # Bildirimler
        await self.broadcast_user_joined(room_id, user_name, websocket)
        await self.send_current_state(websocket, room_id)
        await self.broadcast_user_list(room_id)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """Kullanıcıyı odadan çıkarır"""
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                user_info = self.active_connections[room_id][websocket]
                user_name = user_info["name"]
                
                del self.active_connections[room_id][websocket]
                
                # Kullanıcı listesinden tamamen silmek yerine "online" durumunu değiştirebilirsiniz
                # Ama şimdilik listeden siliyoruz:
                if room_id in self.room_states:
                    self.room_states[room_id]["users"] = [
                        u for u in self.room_states[room_id]["users"]
                        if u["id"] != user_info["id"]
                    ]
                
                logger.info(f"Kullanıcı '{user_name}' '{room_id}' odasından ayrıldı")
                
                asyncio.create_task(self.broadcast_user_left(room_id, user_name))
                asyncio.create_task(self.broadcast_user_list(room_id))

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Mesaj gönderme hatası: {e}")
    
    async def broadcast(self, message: dict, room_id: str, exclude_websocket: WebSocket = None):
        if room_id not in self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections[room_id]:
            if websocket != exclude_websocket:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Yayın hatası: {e}")
                    disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws, room_id)
    
    async def broadcast_user_joined(self, room_id: str, user_name: str, exclude_websocket: WebSocket):
        message = {
            "type": "user_joined",
            "user_name": user_name,
            "message": f"{user_name} odaya katıldı"
        }
        await self.broadcast(message, room_id, exclude_websocket)
    
    async def broadcast_user_left(self, room_id: str, user_name: str):
        message = {
            "type": "user_left",
            "user_name": user_name,
            "message": f"{user_name} odadan ayrıldı"
        }
        await self.broadcast(message, room_id)
    
    async def broadcast_user_list(self, room_id: str):
        """Kullanıcı listesini PUANA GÖRE SIRALAYIP gönderir"""
        if room_id not in self.room_states:
            return
        
        users = self.room_states[room_id]["users"]
        
        # Puanı (total_seconds) yüksek olanı en başa al (reverse=True)
        # get("total_seconds", 0) kullanımı eski veriler varsa hata almamak için
        sorted_users = sorted(users, key=lambda x: x.get("total_seconds", 0), reverse=True)
        
        user_list = [
            {
                "name": user["name"], 
                "id": user["id"],
                "total_seconds": user.get("total_seconds", 0) # Frontend'e puanı gönder
            }
            for user in sorted_users
        ]
        
        message = {
            "type": "user_list_update",
            "users": user_list
        }
        
        if room_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[room_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    disconnected.append(websocket)
            
            for ws in disconnected:
                self.disconnect(ws, room_id)
    
    async def send_current_state(self, websocket: WebSocket, room_id: str):
        """Yeni bağlanan kullanıcıya mevcut timer durumunu gönderir (UTC FIX)"""
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        settings = self.room_states[room_id]["settings"]
        
        remaining = timer_state["remaining_seconds"]
        target_ts = timer_state["target_timestamp"]
        
        if timer_state["is_running"] and target_ts:
            try:
                target_time = datetime.fromisoformat(target_ts)
                now = datetime.now(timezone.utc) # UTC Fix
                remaining = max(0, int((target_time - now).total_seconds()))
            except Exception as e:
                logger.error(f"Timestamp hesaplama hatası: {e}")
                remaining = timer_state["remaining_seconds"]
        
        message = {
            "type": "timer_state",
            "remaining_seconds": remaining,
            "is_running": timer_state["is_running"],
            "target_timestamp": target_ts,
            "mode": timer_state["mode"],
            "settings": settings
        }
        
        await self.send_personal_message(message, websocket)
    
    async def start_timer(self, room_id: str):
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        if timer_state["is_running"]:
            return
        
        remaining = timer_state["remaining_seconds"]
        
        # --- PUANLAMA İÇİN BAŞLANGIÇ GÜNCELLEMESİ ---
        # Timer başlarken odadaki herkesin "session_start" zamanını güncelle
        now = datetime.now(timezone.utc)
        for user in self.room_states[room_id]["users"]:
            user["current_session_start"] = now.isoformat()
        # -------------------------------------------

        # Eğer target_timestamp varsa ve geçmişteyse kontrolü
        if timer_state["target_timestamp"]:
            try:
                target_time = datetime.fromisoformat(timer_state["target_timestamp"])
                if target_time > now:
                    remaining = int((target_time - now).total_seconds())
                else:
                    remaining = 0
            except:
                pass
        
        # Target timestamp hesapla
        target_time = now + timedelta(seconds=remaining)
        target_timestamp = target_time.isoformat()
        
        timer_state["is_running"] = True
        timer_state["target_timestamp"] = target_timestamp
        timer_state["remaining_seconds"] = remaining
        
        message = {
            "type": "timer_started",
            "remaining_seconds": remaining,
            "target_timestamp": target_timestamp,
            "is_running": True,
            "mode": timer_state["mode"]
        }
        await self.broadcast(message, room_id)
    
    async def stop_timer(self, room_id: str):
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        if not timer_state["is_running"]:
            return
        
        remaining = timer_state["remaining_seconds"]
        if timer_state["target_timestamp"]:
            try:
                target_time = datetime.fromisoformat(timer_state["target_timestamp"])
                now = datetime.now(timezone.utc)
                remaining = max(0, int((target_time - now).total_seconds()))
            except:
                pass
        
        # Timer durduğunda session start'ı sıfırla ki hatalı hesap olmasın
        for user in self.room_states[room_id]["users"]:
            user["current_session_start"] = None

        timer_state["is_running"] = False
        timer_state["remaining_seconds"] = remaining
        timer_state["target_timestamp"] = None
        
        message = {
            "type": "timer_stopped",
            "remaining_seconds": remaining,
            "is_running": False,
            "mode": timer_state["mode"]
        }
        await self.broadcast(message, room_id)

    async def finish_timer_and_reward(self, room_id: str):
        """
        Timer bittiğinde kullanıcılara ADİL puan verir.
        Kullanıcının ne kadar süre içeride kaldığını hesaplar.
        """
        if room_id not in self.room_states:
            return
            
        timer_state = self.room_states[room_id]["timer"]
        
        # Sadece timer çalışıyorsa puan ver
        if not timer_state["is_running"]:
            return

        mode = timer_state["mode"]
        settings = self.room_states[room_id]["settings"]
        
        # O seansın maksimum süresi (örn: 25 dk = 1500 sn)
        max_duration = 0
        if mode == "work":
            max_duration = settings["work_duration"]
        elif mode == "short_break":
            max_duration = settings["short_break"]
        elif mode == "long_break":
            max_duration = settings["long_break"]

        now = datetime.now(timezone.utc)
            
        # Her kullanıcı için özel hesaplama yap
        for user in self.room_states[room_id]["users"]:
            # Eğer kullanıcının bir başlangıç zamanı varsa hesapla
            if user.get("current_session_start"):
                try:
                    start_time = datetime.fromisoformat(user["current_session_start"])
                    # Kullanıcının içeride kaldığı süre (saniye)
                    elapsed_seconds = int((now - start_time).total_seconds())
                    
                    # Kullanıcı en fazla timer süresi kadar puan alabilir
                    earned_seconds = min(elapsed_seconds, max_duration)
                    earned_seconds = max(0, earned_seconds)
                    
                    # Puanı ekle (Sadece work modunda veya hepsinde, tercihe bağlı)
                    # Şimdilik hepsinde ekliyoruz:
                    user["total_seconds"] = user.get("total_seconds", 0) + earned_seconds
                        
                except Exception as e:
                    logger.error(f"Puan hesaplama hatası: {e}")
            
            # Bir sonraki tur için başlangıç zamanını sıfırla
            user["current_session_start"] = None
            
        # Timer'ı durdur ve sıfırla
        timer_state["is_running"] = False
        timer_state["target_timestamp"] = None
        timer_state["remaining_seconds"] = 0 # Sıfıra çek
        
        # Puanlar değiştiği için listeyi GÜNCELLE (Sıralı şekilde gider)
        await self.broadcast_user_list(room_id)
        
        # Timer'ın bittiğini bildir
        message = {
            "type": "timer_finished",
            "mode": mode
        }
        await self.broadcast(message, room_id)
    
    async def reset_timer(self, room_id: str, mode: str = "work"):
        """Timer'ı sıfırlar"""
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        settings = self.room_states[room_id]["settings"]
        
        if mode == "work":
            duration = settings["work_duration"]
        elif mode == "short_break":
            duration = settings["short_break"]
        elif mode == "long_break":
            duration = settings["long_break"]
        else:
            duration = settings["work_duration"]
            
        # Session startları sıfırla
        for user in self.room_states[room_id]["users"]:
            user["current_session_start"] = None
        
        timer_state["remaining_seconds"] = duration
        timer_state["is_running"] = False
        timer_state["target_timestamp"] = None
        timer_state["mode"] = mode
        
        message = {
            "type": "timer_reset",
            "remaining_seconds": duration,
            "is_running": False,
            "mode": mode
        }
        await self.broadcast(message, room_id)
    
    async def update_settings(self, room_id: str, work_duration: int, short_break: int, long_break: int):
        if room_id not in self.room_states:
            return
        
        settings = self.room_states[room_id]["settings"]
        settings["work_duration"] = work_duration
        settings["short_break"] = short_break
        settings["long_break"] = long_break
        
        timer_state = self.room_states[room_id]["timer"]
        if not timer_state["is_running"]:
            if timer_state["mode"] == "work":
                timer_state["remaining_seconds"] = work_duration
            elif timer_state["mode"] == "short_break":
                timer_state["remaining_seconds"] = short_break
            elif timer_state["mode"] == "long_break":
                timer_state["remaining_seconds"] = long_break
        
        message = {
            "type": "settings_updated",
            "settings": settings,
            "remaining_seconds": timer_state["remaining_seconds"],
            "mode": timer_state["mode"]
        }
        await self.broadcast(message, room_id)


# Global ConnectionManager instance
manager = ConnectionManager()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Template hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Template yükleme hatası: {str(e)}")


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def read_room(request: Request, room_id: str):
    try:
        return templates.TemplateResponse("index.html", {"request": request, "room_id": room_id})
    except Exception as e:
        logger.error(f"Template hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Template yükleme hatası: {str(e)}")


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    user_name = None
    try:
        await websocket.accept()
        data = await websocket.receive_json()
        user_name = data.get("user_name", "Anonim")
        
        await manager.connect(websocket, room_id, user_name)
        
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "start_timer":
                    await manager.start_timer(room_id)
                elif message_type == "stop_timer":
                    await manager.stop_timer(room_id)
                elif message_type == "reset_timer":
                    mode = data.get("mode", "work")
                    await manager.reset_timer(room_id, mode)
                elif message_type == "update_settings":
                    work_duration = data.get("work_duration", DEFAULT_WORK_DURATION)
                    short_break = data.get("short_break", DEFAULT_SHORT_BREAK)
                    long_break = data.get("long_break", DEFAULT_LONG_BREAK)
                    await manager.update_settings(room_id, work_duration, short_break, long_break)
                
                # YENİ: Frontend'den gelen "Süre Bitti" sinyali
                elif message_type == "timer_completed":
                    await manager.finish_timer_and_reward(room_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Mesaj işleme hatası: {e}")
                break
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket hatası: {e}")
    finally:
        if user_name:
            manager.disconnect(websocket, room_id)


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)