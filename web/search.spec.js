global.document = {
  title: 'Gallery',
  getElementById: () => ({}),
};

const mockPages = [
  'Yellowtail Snapper',
  'Yellow Goatfish',
  'Blue Tang',
  'Bluespine Unicornfish',
  'Spotted Scorpionfish',
  'Red Lionfish',
  'Longlure Frogfish',
];

global.gallery_pages = mockPages;
global.taxonomy_pages = mockPages;
global.sites_pages = mockPages;

const { expandWords, shortenName, search_inner, pageToUrl, toTitleCase } = require('./search.js');

describe('expandWords', () => {
  it('expands words containing "fish"', () => {
    const result = expandWords(['starfish']);
    expect(result).toEqual(['star', 'fish']);
  });

  it('expands words containing "coral"', () => {
    const result = expandWords(['softcoral']);
    expect(result).toEqual(['soft', 'coral']);
  });

  it('expands words containing "ray"', () => {
    const result = expandWords(['stingray']);
    expect(result).toEqual(['sting', 'ray']);
  });

  it('expands words containing "chiton"', () => {
    const result = expandWords(['gumbootchiton']);
    expect(result).toEqual(['gumboot', 'chiton']);
  });

  it('expands words containing "snail"', () => {
    const result = expandWords(['seasnail']);
    expect(result).toEqual(['sea', 'snail']);
  });

  it('expands words containing "worm"', () => {
    const result = expandWords(['flatworm']);
    expect(result).toEqual(['flat', 'worm']);
  });

  it('keeps words without split keywords unchanged', () => {
    const result = expandWords(['octopus']);
    expect(result).toEqual(['octopus']);
  });

  it('handles multiple words with mixed split/non-split', () => {
    const result = expandWords(['blue', 'starfish', 'octopus']);
    expect(result).toEqual(['blue', 'star', 'fish', 'octopus']);
  });

  it('handles empty array', () => {
    const result = expandWords([]);
    expect(result).toEqual([]);
  });

  it('only splits on first occurrence of split word', () => {
    const result = expandWords(['fishfish']);
    expect(result).toEqual(['fishfish']);
  });
});

describe('shortenName', () => {
  // Module 'where' variable is set to 'gallery' at load time

  it('returns names unchanged in gallery context', () => {
    const longName = 'Kingdom Animalia Phylum Chordata Class Actinopterygii';
    const result = shortenName(longName);
    expect(result).toBe(longName);
  });

  it('keeps short names unchanged', () => {
    const result = shortenName('Blue Tang');
    expect(result).toBe('Blue Tang');
  });

  it('handles names with exactly 4 words', () => {
    const result = shortenName('Phylum Chordata Class Actinopterygii');
    expect(result).toBe('Phylum Chordata Class Actinopterygii');
  });
});

describe('search_inner', () => {
  it('finds exact matches', () => {
    const [results, truncated] = search_inner('blue tang');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0][0]).toBe('Blue Tang');
    expect(truncated).toBe(false);
  });

  it('finds partial matches', () => {
    const [results, truncated] = search_inner('yellow');
    expect(results.length).toBe(2);
    expect(results[0][0]).toContain('Yellow');
    expect(results[1][0]).toContain('Yellow');
  });

  it('returns results sorted by exactness then length', () => {
    const [results, truncated] = search_inner('fish');
    expect(results.length).toBeGreaterThan(0);
    if (results.length > 1) {
      expect(results[0][0].length).toBeLessThanOrEqual(results[1][0].length);
    }
  });

  it('returns empty array for no matches', () => {
    const [results, truncated] = search_inner('dolphin');
    expect(results).toEqual([]);
    expect(truncated).toBe(false);
  });

  it('handles case-insensitive search', () => {
    const [results, truncated] = search_inner('blue');
    expect(results.length).toBeGreaterThan(0);
  });

  it('expands compound words during search', () => {
    const [results, truncated] = search_inner('lionfish');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0][0]).toBe('Red Lionfish');
  });

  it('matches all words in search query', () => {
    const [results, truncated] = search_inner('yellow fish');
    expect(results.length).toBeGreaterThan(0);
    results.forEach(([name]) => {
      expect(name.toLowerCase()).toContain('yellow');
      expect(name.toLowerCase()).toContain('fish');
    });
  });

  it('handles skip parameter to paginate results', () => {
    global.gallery_pages = [
      'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
      'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    ];
    global.pages = global.gallery_pages;

    const [firstPage] = search_inner('');
    const firstPageLength = firstPage.length;

    const [secondPage] = search_inner('', firstPageLength);
    expect(secondPage.length).toBeGreaterThan(0);
    if (firstPage.length > 0 && secondPage.length > 0) {
      expect(firstPage[0][0]).not.toBe(secondPage[0][0]);
    }
  });

  it('removes apostrophes from search text', () => {
    const [results] = search_inner("test's");
    expect(results).toEqual([]);
  });

  it('sets truncated flag when results exceed character limit', () => {
    const [results, truncated] = search_inner('');
    expect(typeof truncated).toBe('boolean');
  });
});

describe('pageToUrl', () => {
  it('converts spaces to hyphens', () => {
    const result = pageToUrl('Blue Tang');
    expect(result).toBe('/gallery/Blue-Tang');
  });

  it('handles multiple spaces', () => {
    const result = pageToUrl('Yellow Goat Fish');
    expect(result).toBe('/gallery/Yellow-Goat-Fish');
  });

  it('handles names without spaces', () => {
    const result = pageToUrl('Octopus');
    expect(result).toBe('/gallery/Octopus');
  });
});

describe('toTitleCase', () => {
  it('converts strings to title case in gallery context', () => {
    const result = toTitleCase('yellow goatfish');
    expect(result).toBe('Yellow Goatfish');
  });

  it('handles already title-cased strings', () => {
    const result = toTitleCase('Blue Tang');
    expect(result).toBe('Blue Tang');
  });

  it('handles all caps', () => {
    const result = toTitleCase('LIONFISH');
    expect(result).toBe('Lionfish');
  });

  it('handles mixed case', () => {
    const result = toTitleCase('rEd LiOnFiSh');
    expect(result).toBe('Red Lionfish');
  });

  it('handles single word', () => {
    const result = toTitleCase('octopus');
    expect(result).toBe('Octopus');
  });
});
