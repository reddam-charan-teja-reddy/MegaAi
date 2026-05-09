import '@testing-library/jest-dom';

// JSDOM does not implement canvas, so stub minimal APIs used in tests.
HTMLCanvasElement.prototype.getContext = () => ({
	drawImage: () => {},
	clearRect: () => {},
	getImageData: () => ({ data: [] }),
	putImageData: () => {},
	createImageData: () => [],
	setTransform: () => {},
	save: () => {},
	restore: () => {},
	beginPath: () => {},
	moveTo: () => {},
	lineTo: () => {},
	closePath: () => {},
	stroke: () => {},
	translate: () => {},
	scale: () => {},
	rotate: () => {},
	arc: () => {},
	fill: () => {},
	fillRect: () => {},
	strokeRect: () => {},
});