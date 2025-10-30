global.document = {
  getElementById: () => ({
    value: '0',
  }),
};

const { random, shuffle } = require('./game.js');

describe('random', () => {
  it('returns a value between 0 and maximum', () => {
    const max = 10;
    for (let i = 0; i < 100; i++) {
      const result = random(max);
      expect(result).toBeGreaterThanOrEqual(0);
      expect(result).toBeLessThan(max);
    }
  });

  it('returns 0 for maximum of 1', () => {
    const result = random(1);
    expect(result).toBe(0);
  });

  it('handles large maximum values', () => {
    const max = 1000;
    const result = random(max);
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThan(max);
  });

  it('returns integers only', () => {
    for (let i = 0; i < 50; i++) {
      const result = random(100);
      expect(Number.isInteger(result)).toBe(true);
    }
  });

  it('produces different values across calls', () => {
    const results = new Set();
    const max = 100;
    for (let i = 0; i < 50; i++) {
      results.add(random(max));
    }
    expect(results.size).toBeGreaterThan(10);
  });
});

describe('shuffle', () => {
  it('returns an array of the same length', () => {
    const input = [1, 2, 3, 4, 5];
    const result = shuffle(input);
    expect(result.length).toBe(input.length);
  });

  it('contains all original elements', () => {
    const input = [1, 2, 3, 4, 5];
    const result = shuffle(input);
    expect(result.sort()).toEqual(input.sort());
  });

  it('does not modify the original array', () => {
    const input = [1, 2, 3, 4, 5];
    const original = [...input];
    shuffle(input);
    expect(input).toEqual(original);
  });

  it('handles empty array', () => {
    const result = shuffle([]);
    expect(result).toEqual([]);
  });

  it('handles single element array', () => {
    const result = shuffle([42]);
    expect(result).toEqual([42]);
  });

  it('handles arrays with duplicate values', () => {
    const input = [1, 1, 2, 2, 3, 3];
    const result = shuffle(input);
    expect(result.sort()).toEqual(input.sort());
  });

  it('handles arrays with different types', () => {
    const input = ['a', 1, true, null, {x: 1}];
    const result = shuffle(input);
    expect(result.length).toBe(input.length);
    input.forEach(item => {
      expect(result.includes(item)).toBe(true);
    });
  });

  it('produces different orderings across calls', () => {
    const input = [1, 2, 3, 4, 5, 6, 7, 8];
    const orderings = new Set();

    for (let i = 0; i < 20; i++) {
      orderings.add(JSON.stringify(shuffle(input)));
    }

    expect(orderings.size).toBeGreaterThan(5);
  });
});

// find_similar and choose_correct depend on module-level state and are not easily unit-testable
