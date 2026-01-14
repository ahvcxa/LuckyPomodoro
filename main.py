"""
Gelişmiş Multiplayer Pomodoro Uygulaması
FastAPI + WebSockets ile gerçek zamanlı senkronize Pomodoro sayacı
Target Timestamp mantığı ile doğru zamanlama
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
import uuid
import asyncio
from datetime import datetime, timedelta
import logging

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI uygulaması
app = FastAPI(title="Multiplayer Pomodoro 🍀")

# Templates klasörü
templates = Jinja2Templates(directory="templates")

# Varsayılan Pomodoro ayarları (saniye cinsinden)
DEFAULT_WORK_DURATION = 25 * 60      # 25 dakika
DEFAULT_SHORT_BREAK = 5 * 60         # 5 dakika
DEFAULT_LONG_BREAK = 15 * 60         # 15 dakika


class ConnectionManager:
    """
    WebSocket bağlantılarını ve oda durumlarını yöneten sınıf.
    Her oda için ayrı bağlantı listesi ve timer durumu tutar.
    Target Timestamp mantığı ile doğru zamanlama sağlar.
    """
    
    def __init__(self):
        # Her oda için aktif bağlantılar: {room_id: {websocket: user_info}}
        self.active_connections: Dict[str, Dict[WebSocket, dict]] = {}
        # Oda durumları: {room_id: room_state}
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
                    "target_timestamp": None,  # Bitiş zamanı (timestamp)
                    "mode": "work"  # work, short_break, long_break
                },
                "settings": {
                    "work_duration": DEFAULT_WORK_DURATION,
                    "short_break": DEFAULT_SHORT_BREAK,
                    "long_break": DEFAULT_LONG_BREAK
                },
                "users": []
            }
        
        # Kullanıcı bilgisini kaydet
        user_info = {
            "name": user_name,
            "id": str(uuid.uuid4()),
            "joined_at": datetime.now().isoformat()
        }
        self.active_connections[room_id][websocket] = user_info
        
        # Kullanıcı listesine ekle (eğer daha önce eklenmemişse)
        existing_user = next(
            (u for u in self.room_states[room_id]["users"] if u["id"] == user_info["id"]),
            None
        )
        if not existing_user:
            self.room_states[room_id]["users"].append(user_info)
        
        logger.info(f"Kullanıcı '{user_name}' '{room_id}' odasına katıldı")
        
        # Odadaki diğer kullanıcılara bildir
        await self.broadcast_user_joined(room_id, user_name, websocket)
        
        # Yeni kullanıcıya mevcut durumu gönder
        await self.send_current_state(websocket, room_id)
        
        # Kullanıcı listesini güncelle
        await self.broadcast_user_list(room_id)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """Kullanıcıyı odadan çıkarır"""
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                user_info = self.active_connections[room_id][websocket]
                user_name = user_info["name"]
                
                # Bağlantıyı kaldır
                del self.active_connections[room_id][websocket]
                
                # Kullanıcı listesinden çıkar
                if room_id in self.room_states:
                    self.room_states[room_id]["users"] = [
                        u for u in self.room_states[room_id]["users"]
                        if u["id"] != user_info["id"]
                    ]
                
                logger.info(f"Kullanıcı '{user_name}' '{room_id}' odasından ayrıldı")
                
                # Eğer odada kimse kalmadıysa odayı temizle (opsiyonel)
                if len(self.active_connections[room_id]) == 0:
                    # Odayı tamamen silmek isterseniz:
                    # del self.room_states[room_id]
                    # del self.active_connections[room_id]
                    pass
                
                # Diğer kullanıcılara bildir
                asyncio.create_task(self.broadcast_user_left(room_id, user_name))
                asyncio.create_task(self.broadcast_user_list(room_id))
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Belirli bir kullanıcıya mesaj gönderir"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Mesaj gönderme hatası: {e}")
    
    async def broadcast(self, message: dict, room_id: str, exclude_websocket: WebSocket = None):
        """Odadaki tüm kullanıcılara mesaj gönderir (belirli bir kullanıcı hariç)"""
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
        
        # Bağlantısı kopan websocket'leri temizle
        for ws in disconnected:
            self.disconnect(ws, room_id)
    
    async def broadcast_user_joined(self, room_id: str, user_name: str, exclude_websocket: WebSocket):
        """Yeni kullanıcı katıldı bildirimi"""
        message = {
            "type": "user_joined",
            "user_name": user_name,
            "message": f"{user_name} odaya katıldı"
        }
        await self.broadcast(message, room_id, exclude_websocket)
    
    async def broadcast_user_left(self, room_id: str, user_name: str):
        """Kullanıcı ayrıldı bildirimi"""
        message = {
            "type": "user_left",
            "user_name": user_name,
            "message": f"{user_name} odadan ayrıldı"
        }
        await self.broadcast(message, room_id)
    
    async def broadcast_user_list(self, room_id: str):
        """Kullanıcı listesini tüm odadaki kullanıcılara gönderir"""
        if room_id not in self.room_states:
            return
        
        user_list = [
            {"name": user["name"], "id": user["id"]}
            for user in self.room_states[room_id]["users"]
        ]
        
        message = {
            "type": "user_list_update",
            "users": user_list
        }
        
        # Tüm kullanıcılara gönder
        if room_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[room_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Kullanıcı listesi gönderme hatası: {e}")
                    disconnected.append(websocket)
            
            for ws in disconnected:
                self.disconnect(ws, room_id)
    
    async def send_current_state(self, websocket: WebSocket, room_id: str):
        """Yeni bağlanan kullanıcıya mevcut timer durumunu gönderir"""
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        settings = self.room_states[room_id]["settings"]
        
        # Target timestamp varsa, kalan süreyi hesapla
        remaining = timer_state["remaining_seconds"]
        target_ts = timer_state["target_timestamp"]
        
        if timer_state["is_running"] and target_ts:
            try:
                target_time = datetime.fromisoformat(target_ts)
                now = datetime.now()
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
        """Timer'ı başlatır - Target timestamp hesaplar"""
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        
        # Eğer timer zaten çalışıyorsa, hiçbir şey yapma
        if timer_state["is_running"]:
            return
        
        # Mevcut kalan süreyi al
        remaining = timer_state["remaining_seconds"]
        
        # Eğer target_timestamp varsa ve geçmişteyse, kalan süreyi güncelle
        if timer_state["target_timestamp"]:
            try:
                target_time = datetime.fromisoformat(timer_state["target_timestamp"])
                now = datetime.now()
                if target_time > now:
                    remaining = int((target_time - now).total_seconds())
                else:
                    remaining = 0
            except:
                pass
        
        # Target timestamp hesapla (şu anki zaman + kalan süre)
        now = datetime.now()
        target_time = now + timedelta(seconds=remaining)
        target_timestamp = target_time.isoformat()
        
        # Timer durumunu güncelle
        timer_state["is_running"] = True
        timer_state["target_timestamp"] = target_timestamp
        timer_state["remaining_seconds"] = remaining  # Güncel kalan süre
        
        # Tüm kullanıcılara bildir
        message = {
            "type": "timer_started",
            "remaining_seconds": remaining,
            "target_timestamp": target_timestamp,
            "is_running": True,
            "mode": timer_state["mode"]
        }
        await self.broadcast(message, room_id)
    
    async def stop_timer(self, room_id: str):
        """Timer'ı durdurur - Kalan süreyi hesaplayıp kaydeder"""
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        
        if not timer_state["is_running"]:
            return
        
        # Kalan süreyi hesapla (target_timestamp'tan)
        remaining = timer_state["remaining_seconds"]
        if timer_state["target_timestamp"]:
            try:
                target_time = datetime.fromisoformat(timer_state["target_timestamp"])
                now = datetime.now()
                remaining = max(0, int((target_time - now).total_seconds()))
            except:
                pass
        
        # Timer durumunu güncelle
        timer_state["is_running"] = False
        timer_state["remaining_seconds"] = remaining
        timer_state["target_timestamp"] = None
        
        # Tüm kullanıcılara bildir
        message = {
            "type": "timer_stopped",
            "remaining_seconds": remaining,
            "is_running": False,
            "mode": timer_state["mode"]
        }
        await self.broadcast(message, room_id)
    
    async def reset_timer(self, room_id: str, mode: str = "work"):
        """Timer'ı sıfırlar - Seçilen moda göre süreyi ayarlar"""
        if room_id not in self.room_states:
            return
        
        timer_state = self.room_states[room_id]["timer"]
        settings = self.room_states[room_id]["settings"]
        
        # Moda göre süreyi belirle
        if mode == "work":
            duration = settings["work_duration"]
        elif mode == "short_break":
            duration = settings["short_break"]
        elif mode == "long_break":
            duration = settings["long_break"]
        else:
            duration = settings["work_duration"]
        
        timer_state["remaining_seconds"] = duration
        timer_state["is_running"] = False
        timer_state["target_timestamp"] = None
        timer_state["mode"] = mode
        
        # Tüm kullanıcılara bildir
        message = {
            "type": "timer_reset",
            "remaining_seconds": duration,
            "is_running": False,
            "mode": mode
        }
        await self.broadcast(message, room_id)
    
    async def update_settings(self, room_id: str, work_duration: int, short_break: int, long_break: int):
        """Oda ayarlarını günceller"""
        if room_id not in self.room_states:
            return
        
        settings = self.room_states[room_id]["settings"]
        settings["work_duration"] = work_duration
        settings["short_break"] = short_break
        settings["long_break"] = long_break
        
        # Eğer timer çalışmıyorsa, mevcut moda göre süreyi güncelle
        timer_state = self.room_states[room_id]["timer"]
        if not timer_state["is_running"]:
            if timer_state["mode"] == "work":
                timer_state["remaining_seconds"] = work_duration
            elif timer_state["mode"] == "short_break":
                timer_state["remaining_seconds"] = short_break
            elif timer_state["mode"] == "long_break":
                timer_state["remaining_seconds"] = long_break
        
        # Tüm kullanıcılara bildir
        message = {
            "type": "settings_updated",
            "settings": settings,
            "remaining_seconds": timer_state["remaining_seconds"],
            "mode": timer_state["mode"]
        }
        await self.broadcast(message, room_id)


# Global ConnectionManager instance
manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Ana sayfa"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def read_room(request: Request, room_id: str):
    """Oda sayfası"""
    return templates.TemplateResponse("index.html", {"request": request, "room_id": room_id})


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint'i - Her oda için ayrı bağlantı
    """
    user_name = None
    
    try:
        # WebSocket bağlantısını kabul et
        await websocket.accept()
        
        # İlk mesaj kullanıcı adını içermeli
        data = await websocket.receive_json()
        user_name = data.get("user_name", "Anonim")
        
        # Bağlantıyı kur
        await manager.connect(websocket, room_id, user_name)
        
        # Mesaj dinleme döngüsü
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
        # Bağlantıyı kapat
        if user_name:
            manager.disconnect(websocket, room_id)


if __name__ == "__main__":
    import uvicorn
    import os
    # PORT environment variable'ını kontrol et (hosting platformları için)
    port = int(os.environ.get("PORT", 8000))
    # 0.0.0.0 ile yerel ağdaki cihazlardan erişilebilir
    uvicorn.run(app, host="0.0.0.0", port=port)
