/**
 * PolygonDrawer - Canvas 기반 다각형/프리핸드 드로잉 클래스
 *
 * 개선사항:
 * - 프리핸드: 여러 번 나눠 그리기 가능 (stroke 단위 undo)
 * - 다각형: 커서 따라가는 미리보기 선
 */
class PolygonDrawer {
  constructor(canvasEl, imageSrc, onComplete) {
    this.canvas = canvasEl;
    this.ctx = canvasEl.getContext('2d');
    this.onComplete = onComplete;

    this.mode = 'polygon'; // 'polygon' | 'freehand'
    this.points = [];       // 다각형 모드용
    this.strokes = [];      // 프리핸드 모드: [[pt, pt, ...], [pt, pt, ...]]
    this.currentStroke = []; // 프리핸드: 현재 그리고 있는 획
    this.isDrawing = false;
    this.isClosed = false;
    this.scale = 1;
    this.image = null;
    this.imageWidth = 0;
    this.imageHeight = 0;
    this.cursorPos = null;  // 다각형 모드: 마우스 현재 위치

    // 스타일
    this.strokeColor = '#F4B900';
    this.fillColor = 'rgba(244, 185, 0, 0.15)';
    this.pointRadius = 6;
    this.closeThreshold = 15;

    this._handlers = {};
    this._loadImage(imageSrc);
  }

  _loadImage(src) {
    this.image = new Image();
    this.image.crossOrigin = 'anonymous';
    this.image.onload = () => {
      this.imageWidth = this.image.naturalWidth;
      this.imageHeight = this.image.naturalHeight;

      const container = this.canvas.parentElement;
      const maxW = container ? container.clientWidth : 500;
      this.scale = Math.min(maxW / this.imageWidth, 1);

      this.canvas.width = Math.round(this.imageWidth * this.scale);
      this.canvas.height = Math.round(this.imageHeight * this.scale);

      this._draw();
      this._bindEvents();
    };
    this.image.src = src;
  }

  _getCanvasPoint(event) {
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = this.canvas.width / rect.width;
    const scaleY = this.canvas.height / rect.height;

    let clientX, clientY;
    if (event.touches && event.touches.length > 0) {
      clientX = event.touches[0].clientX;
      clientY = event.touches[0].clientY;
    } else {
      clientX = event.clientX;
      clientY = event.clientY;
    }

    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY,
    };
  }

  _toImageCoords(pts) {
    return pts.map(p => [
      Math.round(p.x / this.scale),
      Math.round(p.y / this.scale),
    ]);
  }

  /** 프리핸드 모든 stroke를 하나의 점 배열로 합침 */
  _getAllFreehandPoints() {
    var all = [];
    for (var i = 0; i < this.strokes.length; i++) {
      for (var j = 0; j < this.strokes[i].length; j++) {
        all.push(this.strokes[i][j]);
      }
    }
    // 현재 그리는 중인 획도 포함
    for (var k = 0; k < this.currentStroke.length; k++) {
      all.push(this.currentStroke[k]);
    }
    return all;
  }

  _draw() {
    var ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // 배경 이미지
    if (this.image && this.image.complete) {
      ctx.drawImage(this.image, 0, 0, this.canvas.width, this.canvas.height);
    }

    if (this.mode === 'polygon') {
      this._drawPolygon(ctx);
    } else {
      this._drawFreehand(ctx);
    }
  }

  _drawPolygon(ctx) {
    if (this.points.length === 0) return;

    // 경로 그리기
    ctx.beginPath();
    ctx.moveTo(this.points[0].x, this.points[0].y);
    for (var i = 1; i < this.points.length; i++) {
      ctx.lineTo(this.points[i].x, this.points[i].y);
    }

    // 닫힌 상태면 채우기
    if (this.isClosed) {
      ctx.closePath();
      ctx.fillStyle = this.fillColor;
      ctx.fill();
    } else if (this.cursorPos && this.points.length > 0) {
      // 미리보기 선: 마지막 점 → 커서
      ctx.lineTo(this.cursorPos.x, this.cursorPos.y);
      // 첫 점까지 점선 미리보기
      ctx.setLineDash([4, 4]);
      ctx.lineTo(this.points[0].x, this.points[0].y);
    }

    ctx.strokeStyle = this.strokeColor;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.stroke();
    ctx.setLineDash([]);

    // 꼭짓점 표시
    for (var j = 0; j < this.points.length; j++) {
      var p = this.points[j];
      ctx.beginPath();
      ctx.arc(p.x, p.y, this.pointRadius, 0, Math.PI * 2);
      ctx.fillStyle = j === 0 ? '#ff4444' : this.strokeColor;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    // 첫 점 근처면 닫기 힌트 (확대 원)
    if (!this.isClosed && this.cursorPos && this.points.length >= 3) {
      var first = this.points[0];
      var dist = Math.hypot(this.cursorPos.x - first.x, this.cursorPos.y - first.y);
      if (dist <= this.closeThreshold) {
        ctx.beginPath();
        ctx.arc(first.x, first.y, this.pointRadius + 4, 0, Math.PI * 2);
        ctx.strokeStyle = '#ff4444';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }
  }

  _drawFreehand(ctx) {
    var allPoints = this._getAllFreehandPoints();
    if (allPoints.length === 0) return;

    // 전체 경로
    ctx.beginPath();
    ctx.moveTo(allPoints[0].x, allPoints[0].y);
    for (var i = 1; i < allPoints.length; i++) {
      ctx.lineTo(allPoints[i].x, allPoints[i].y);
    }

    if (this.isClosed) {
      ctx.closePath();
      ctx.fillStyle = this.fillColor;
      ctx.fill();
    }

    ctx.strokeStyle = this.strokeColor;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();

    // 시작점/끝점 표시 (닫히지 않았을 때)
    if (!this.isClosed && allPoints.length > 0) {
      // 시작점
      ctx.beginPath();
      ctx.arc(allPoints[0].x, allPoints[0].y, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#ff4444';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 끝점
      var last = allPoints[allPoints.length - 1];
      ctx.beginPath();
      ctx.arc(last.x, last.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = this.strokeColor;
      ctx.fill();
    }
  }

  // ── 이벤트 ──

  _bindEvents() {
    this._unbindEvents();

    if (this.mode === 'polygon') {
      this._handlers.click = (e) => this._onClickPolygon(e);
      this._handlers.mousemove = (e) => this._onMouseMovePolygon(e);
      this._handlers.mouseleave = () => { this.cursorPos = null; this._draw(); };
      this.canvas.addEventListener('click', this._handlers.click);
      this.canvas.addEventListener('mousemove', this._handlers.mousemove);
      this.canvas.addEventListener('mouseleave', this._handlers.mouseleave);
    } else {
      this._handlers.pointerdown = (e) => this._onPointerDown(e);
      this._handlers.pointermove = (e) => this._onPointerMove(e);
      this._handlers.pointerup = (e) => this._onPointerUp(e);
      this.canvas.addEventListener('pointerdown', this._handlers.pointerdown);
      this.canvas.addEventListener('pointermove', this._handlers.pointermove);
      this.canvas.addEventListener('pointerup', this._handlers.pointerup);
    }

    this._handlers.touchmove = (e) => {
      if (this.isDrawing) e.preventDefault();
    };
    this.canvas.addEventListener('touchmove', this._handlers.touchmove, { passive: false });
  }

  _unbindEvents() {
    if (this._handlers.click) {
      this.canvas.removeEventListener('click', this._handlers.click);
    }
    if (this._handlers.mousemove) {
      this.canvas.removeEventListener('mousemove', this._handlers.mousemove);
      this.canvas.removeEventListener('mouseleave', this._handlers.mouseleave);
    }
    if (this._handlers.pointerdown) {
      this.canvas.removeEventListener('pointerdown', this._handlers.pointerdown);
      this.canvas.removeEventListener('pointermove', this._handlers.pointermove);
      this.canvas.removeEventListener('pointerup', this._handlers.pointerup);
    }
    if (this._handlers.touchmove) {
      this.canvas.removeEventListener('touchmove', this._handlers.touchmove);
    }
    this._handlers = {};
  }

  // ── 다각형 모드 ──

  _onClickPolygon(e) {
    if (this.isClosed) return;

    var pt = this._getCanvasPoint(e);

    if (this.points.length >= 3) {
      var first = this.points[0];
      var dist = Math.hypot(pt.x - first.x, pt.y - first.y);
      if (dist <= this.closeThreshold) {
        this.isClosed = true;
        this.cursorPos = null;
        this._draw();
        return;
      }
    }

    this.points.push(pt);
    this._draw();
  }

  _onMouseMovePolygon(e) {
    if (this.isClosed) return;
    this.cursorPos = this._getCanvasPoint(e);
    this._draw();
  }

  // ── 프리핸드 모드 ──

  _onPointerDown(e) {
    if (this.isClosed) return;
    this.isDrawing = true;
    this.currentStroke = [];
    var pt = this._getCanvasPoint(e);
    this.currentStroke.push(pt);
    this.canvas.setPointerCapture(e.pointerId);
  }

  _onPointerMove(e) {
    if (!this.isDrawing) return;
    var pt = this._getCanvasPoint(e);
    this.currentStroke.push(pt);
    this._draw();
  }

  _onPointerUp(e) {
    if (!this.isDrawing) return;
    this.isDrawing = false;
    this.canvas.releasePointerCapture(e.pointerId);

    // 현재 획을 strokes에 저장
    if (this.currentStroke.length >= 2) {
      this.strokes.push(this.currentStroke);
    }
    this.currentStroke = [];
    this._draw();
  }

  // ── 컨트롤 ──

  setMode(mode) {
    this.mode = mode;
    this.reset();
    this._bindEvents();
  }

  undo() {
    if (this.isClosed) {
      this.isClosed = false;
      this._draw();
      return;
    }
    if (this.mode === 'polygon') {
      this.points.pop();
    } else {
      // 프리핸드: 마지막 획 제거
      this.strokes.pop();
    }
    this._draw();
  }

  /** 영역 닫기 (프리핸드 수동 완료용) */
  close() {
    if (this.mode === 'freehand') {
      var all = this._getAllFreehandPoints();
      if (all.length >= 3) {
        this.isClosed = true;
        this._draw();
        return true;
      }
    }
    return false;
  }

  reset() {
    this.points = [];
    this.strokes = [];
    this.currentStroke = [];
    this.isClosed = false;
    this.isDrawing = false;
    this.cursorPos = null;
    this._draw();
  }

  getImagePoints() {
    if (!this.isClosed) return null;

    var pts;
    if (this.mode === 'polygon') {
      if (this.points.length < 3) return null;
      pts = this.points;
    } else {
      pts = this._getAllFreehandPoints();
      if (pts.length < 3) return null;
      // 점이 너무 많으면 간소화
      if (pts.length > 200) {
        var step = Math.ceil(pts.length / 200);
        pts = pts.filter(function(_, i) { return i % step === 0; });
      }
    }
    return this._toImageCoords(pts);
  }

  destroy() {
    this._unbindEvents();
    this.points = [];
    this.strokes = [];
    this.currentStroke = [];
    this.image = null;
  }
}
