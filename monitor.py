from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):  # Monitora arquivos Python
            print(f'Arquivo modificado: {event.src_path}')
            # Aqui você pode adicionar lógica para recarregar ou modificar o conteúdo

if __name__ == "__main__":
    path = "."  # Diretório atual
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join() 