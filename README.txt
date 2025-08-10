
Liset — учёт листов назначений (двуязычный RU/UZ) — проект с GitHub Actions сборкой .exe

Файлы в репозитории:
- main.py       — приложение (Tkinter, Python 3.8+)
- liset.db      — (создаётся при первом запуске)
- .github/workflows/build.yml  — workflow для сборки Windows .exe через PyInstaller
- README.txt    — эта инструкция
- logo.png      — иконка/логотип (PNG)
Запуск локально:
1) Установите Python 3.8+
2) Откройте командную строку в папке проекта и выполните: python main.py
Создание .exe на GitHub (автоматически после push):
1) Создайте новый репозиторий на GitHub (например, Liset).
2) Загрузите все файлы из этого архива (через Upload files в веб-интерфейсе).
3) В разделе Actions появится workflow "build-windows-exe" — дождитесь его выполнения.
4) В результате в Artifacts появится файл main.exe (или Liset.exe) — скачайте его.
Примечание: workflow использует pyinstaller --onefile (без иконки). Если захотите иконку, я помогу добавить .ico и настроить сборку.
