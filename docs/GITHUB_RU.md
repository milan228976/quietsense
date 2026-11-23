# Публикация на GitHub

Создайте пустой репозиторий `quietsense` без автоматически создаваемого README. В корне распакованного проекта:

```powershell
git init
git add .
git commit -m "Add QuietSense CAD, CAE and CAM portfolio project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/quietsense.git
git push -u origin main
```

Замените `YOUR_USERNAME` своим логином. Если Git запросит имя и email для коммита, настройте их для этого репозитория. Публикация из подготовленного архива автоматически не выполнялась.

Description: `Passive sensor filter: KiCad PCB, nodal simulation, Monte Carlo and manufacturing outputs.`

Topics: `kicad`, `pcb-design`, `analog-electronics`, `circuit-simulation`, `cad`, `cae`, `cam`, `hardware`.

README уже содержит изображения, формулы и ссылки. Для обложки социального предпросмотра можно использовать `docs/images/00-cover.png`.
