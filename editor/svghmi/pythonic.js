/*

From https://github.com/keyvan-m-sadeghi/pythonic

Slightly modified in order to be usable in browser (i.e. not as a node.js module)

The MIT License (MIT)

Copyright (c) 2016 Assister.Ai

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

class Iterator {
    constructor(generator) {
        this[Symbol.iterator] = generator;
    }

    async * [Symbol.asyncIterator]() {
        for (const element of this) {
            yield await element;
        }
    }

    forEach(callback) {
        for (const element of this) {
            callback(element);
        }
    }

    map(callback) {
        const result = [];
        for (const element of this) {
            result.push(callback(element));
        }

        return result;
    }

    filter(callback) {
        const result = [];
        for (const element of this) {
            if (callback(element)) {
                result.push(element);
            }
        }

        return result;
    }

    reduce(callback, initialValue) {
        let empty = typeof initialValue === 'undefined';
        let accumulator = initialValue;
        let index = 0;
        for (const currentValue of this) {
            if (empty) {
                accumulator = currentValue;
                empty = false;
                continue;
            }

            accumulator = callback(accumulator, currentValue, index, this);
            index++;
        }

        if (empty) {
            throw new TypeError('Reduce of empty Iterator with no initial value');
        }

        return accumulator;
    }

    some(callback) {
        for (const element of this) {
            if (callback(element)) {
                return true;
            }
        }

        return false;
    }

    every(callback) {
        for (const element of this) {
            if (!callback(element)) {
                return false;
            }
        }

        return true;
    }

    static fromIterable(iterable) {
        return new Iterator(function * () {
            for (const element of iterable) {
                yield element;
            }
        });
    }

    toArray() {
        return Array.from(this);
    }

    next() {
        if (!this.currentInvokedGenerator) {
            this.currentInvokedGenerator = this[Symbol.iterator]();
        }

        return this.currentInvokedGenerator.next();
    }

    reset() {
        delete this.currentInvokedGenerator;
    }
}

function rangeSimple(stop) {
    return new Iterator(function * () {
        for (let i = 0; i < stop; i++) {
            yield i;
        }
    });
}

function rangeOverload(start, stop, step = 1) {
    return new Iterator(function * () {
        for (let i = start; i < stop; i += step) {
            yield i;
        }
    });
}

function range(...args) {
    if (args.length < 2) {
        return rangeSimple(...args);
    }

    return rangeOverload(...args);
}

function enumerate(iterable) {
    return new Iterator(function * () {
        let index = 0;
        for (const element of iterable) {
            yield [index, element];
            index++;
        }
    });
}

const _zip = longest => (...iterables) => {
    if (iterables.length < 2) {
        throw new TypeError("zip takes 2 iterables at least, "+iterables.length+" given");
    }

    return new Iterator(function * () {
        const iterators = iterables.map(iterable => Iterator.fromIterable(iterable));
        while (true) {
            const row = iterators.map(iterator => iterator.next());
            const check = longest ? row.every.bind(row) : row.some.bind(row);
            if (check(next => next.done)) {
                return;
            }

            yield row.map(next => next.value);
        }
    });
};

const zip = _zip(false), zipLongest= _zip(true);

function items(obj) {
    let {keys, get} = obj;
    if (obj instanceof Map) {
        keys = keys.bind(obj);
        get = get.bind(obj);
    } else {
        keys = function () {
            return Object.keys(obj);
        };

        get = function (key) {
            return obj[key];
        };
    }

    return new Iterator(function * () {
        for (const key of keys()) {
            yield [key, get(key)];
        }
    });
}

/*
module.exports = {Iterator, range, enumerate, zip: _zip(false), zipLongest: _zip(true), items};
*/
