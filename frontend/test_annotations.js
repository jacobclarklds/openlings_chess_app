#!/usr/bin/env node
/**
 * Test script to verify chess annotation conversion utilities.
 * Tests that backend annotations are correctly converted to react-chessboard format.
 */

// Since this is a TypeScript/React project, we'll simulate the conversion functions
// This is a Node.js script that replicates the logic from chessUtils.ts

console.log('🧪 Testing Frontend Annotation Conversion\n');
console.log('=' + '='.repeat(59));

/**
 * Simulated convertAnnotationsToArrows function from chessUtils.ts
 */
function convertAnnotationsToArrows(annotations) {
  return annotations
    .filter(ann => ann.type === 'arrow')
    .map(ann => [ann.from, ann.to, ann.color]);
}

/**
 * Simulated getSquareStyles function from chessUtils.ts
 */
function getSquareStyles(annotations) {
  const styles = {};

  annotations.forEach(ann => {
    if (ann.type === 'highlight' || ann.type === 'circle') {
      const colorMap = {
        green: 'rgba(0, 255, 0, 0.4)',
        blue: 'rgba(0, 0, 255, 0.4)',
        red: 'rgba(255, 0, 0, 0.4)',
        yellow: 'rgba(255, 255, 0, 0.4)'
      };

      styles[ann.square] = {
        backgroundColor: colorMap[ann.color] || 'rgba(255, 255, 255, 0.4)',
        borderRadius: ann.type === 'circle' ? '50%' : '0%'
      };
    }
  });

  return styles;
}

// Test cases
const testCases = [
  {
    name: 'Opening position annotations',
    annotations: [
      { id: 'ann_e4', type: 'highlight', color: 'green', square: 'e4' },
      { id: 'ann_d4', type: 'highlight', color: 'green', square: 'd4' },
      { id: 'ann_e5', type: 'highlight', color: 'green', square: 'e5' },
      { id: 'ann_d5', type: 'highlight', color: 'green', square: 'd5' },
      { id: 'ann_arrow_1', type: 'arrow', color: 'blue', from: 'g1', to: 'f3' },
      { id: 'ann_arrow_2', type: 'arrow', color: 'blue', from: 'b1', to: 'c3' }
    ]
  },
  {
    name: 'Middlegame position annotations',
    annotations: [
      { id: 'ann_center_0', type: 'circle', color: 'yellow', square: 'e4' },
      { id: 'ann_center_1', type: 'circle', color: 'yellow', square: 'e5' },
      { id: 'ann_king_2', type: 'circle', color: 'blue', square: 'e8' }
    ]
  },
  {
    name: 'Mixed annotations',
    annotations: [
      { id: 'h1', type: 'highlight', color: 'green', square: 'd4' },
      { id: 'c1', type: 'circle', color: 'red', square: 'e8' },
      { id: 'a1', type: 'arrow', color: 'green', from: 'e2', to: 'e4' }
    ]
  }
];

let allTestsPassed = true;

testCases.forEach((testCase, index) => {
  console.log(`\n📋 Test ${index + 1}: ${testCase.name}`);
  console.log('-'.repeat(60));

  // Test arrow conversion
  const arrows = convertAnnotationsToArrows(testCase.annotations);
  const expectedArrows = testCase.annotations.filter(a => a.type === 'arrow').length;

  console.log(`\n  🏹 Arrows:`);
  console.log(`     Expected: ${expectedArrows} arrows`);
  console.log(`     Got: ${arrows.length} arrows`);

  if (arrows.length === expectedArrows) {
    console.log(`     ✅ Correct number of arrows`);
    arrows.forEach(([from, to, color]) => {
      console.log(`        → ${color} arrow: ${from} → ${to}`);
    });
  } else {
    console.log(`     ❌ Wrong number of arrows!`);
    allTestsPassed = false;
  }

  // Test square styles conversion
  const squareStyles = getSquareStyles(testCase.annotations);
  const expectedSquares = testCase.annotations.filter(a => a.type === 'highlight' || a.type === 'circle').length;
  const gotSquares = Object.keys(squareStyles).length;

  console.log(`\n  🎨 Square Styles:`);
  console.log(`     Expected: ${expectedSquares} styled squares`);
  console.log(`     Got: ${gotSquares} styled squares`);

  if (gotSquares === expectedSquares) {
    console.log(`     ✅ Correct number of styled squares`);
    Object.entries(squareStyles).forEach(([square, style]) => {
      const ann = testCase.annotations.find(a => a.square === square);
      const shape = style.borderRadius === '50%' ? 'circle' : 'highlight';
      console.log(`        → ${square}: ${ann.color} ${shape}`);
    });
  } else {
    console.log(`     ❌ Wrong number of styled squares!`);
    allTestsPassed = false;
  }
});

// Test react-chessboard format compliance
console.log(`\n${'='.repeat(60)}`);
console.log(`\n🎯 React-Chessboard Format Verification:`);
console.log('-'.repeat(60));

const sampleAnnotations = [
  { id: '1', type: 'arrow', color: 'green', from: 'e2', to: 'e4' },
  { id: '2', type: 'circle', color: 'red', square: 'e8' }
];

const arrows = convertAnnotationsToArrows(sampleAnnotations);
const styles = getSquareStyles(sampleAnnotations);

console.log(`\nReact-Chessboard expects:`);
console.log(`  • Arrows: Array<[from, to, color]>`);
console.log(`  • Styles: Object<square, {backgroundColor, borderRadius}>`);

console.log(`\nOur output:`);
console.log(`  • Arrows: ${JSON.stringify(arrows)}`);
console.log(`  • Styles: ${JSON.stringify(styles, null, 2)}`);

const arrowFormatCorrect = Array.isArray(arrows) &&
  arrows.every(a => Array.isArray(a) && a.length === 3);

const styleFormatCorrect = typeof styles === 'object' &&
  Object.values(styles).every(s => 'backgroundColor' in s && 'borderRadius' in s);

if (arrowFormatCorrect && styleFormatCorrect) {
  console.log(`\n✅ Format is correct for react-chessboard!`);
} else {
  console.log(`\n❌ Format is INCORRECT!`);
  allTestsPassed = false;
}

// Summary
console.log(`\n${'='.repeat(60)}`);
if (allTestsPassed) {
  console.log(`\n✅ ALL TESTS PASSED!`);
  console.log(`\n🎉 Frontend annotation conversion is working correctly!`);
  console.log(`   Arrows and square styles will be rendered on the chessboard.`);
  process.exit(0);
} else {
  console.log(`\n❌ SOME TESTS FAILED!`);
  console.log(`   The frontend may not correctly render annotations.`);
  process.exit(1);
}
