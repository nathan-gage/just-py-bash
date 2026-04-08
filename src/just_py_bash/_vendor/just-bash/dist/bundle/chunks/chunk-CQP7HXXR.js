import {
  formatMode
} from "./chunk-Z4P336UH.js";
import {
  DefenseInDepthBox
} from "./chunk-R3ZPC4XR.js";
import {
  createUserRegex
} from "./chunk-PXYGJXWK.js";
import {
  hasHelpFlag,
  showHelp,
  unknownOption
} from "./chunk-GFRMOA7L.js";
import {
  __commonJS,
  __toESM
} from "./chunk-KH45J4DC.js";

// node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/bitreader.js
var require_bitreader = __commonJS({
  "node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/bitreader.js"(exports, module) {
    var BITMASK = [0, 1, 3, 7, 15, 31, 63, 127, 255];
    var BitReader = function(stream) {
      this.stream = stream;
      this.bitOffset = 0;
      this.curByte = 0;
      this.hasByte = false;
    };
    BitReader.prototype._ensureByte = function() {
      if (!this.hasByte) {
        this.curByte = this.stream.readByte();
        this.hasByte = true;
      }
    };
    BitReader.prototype.read = function(bits) {
      var result = 0;
      while (bits > 0) {
        this._ensureByte();
        var remaining = 8 - this.bitOffset;
        if (bits >= remaining) {
          result <<= remaining;
          result |= BITMASK[remaining] & this.curByte;
          this.hasByte = false;
          this.bitOffset = 0;
          bits -= remaining;
        } else {
          result <<= bits;
          var shift = remaining - bits;
          result |= (this.curByte & BITMASK[bits] << shift) >> shift;
          this.bitOffset += bits;
          bits = 0;
        }
      }
      return result;
    };
    BitReader.prototype.seek = function(pos) {
      var n_bit = pos % 8;
      var n_byte = (pos - n_bit) / 8;
      this.bitOffset = n_bit;
      this.stream.seek(n_byte);
      this.hasByte = false;
    };
    BitReader.prototype.pi = function() {
      var buf = new Buffer(6), i;
      for (i = 0; i < buf.length; i++) {
        buf[i] = this.read(8);
      }
      return buf.toString("hex");
    };
    module.exports = BitReader;
  }
});

// node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/stream.js
var require_stream = __commonJS({
  "node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/stream.js"(exports, module) {
    var Stream = function() {
    };
    Stream.prototype.readByte = function() {
      throw new Error("abstract method readByte() not implemented");
    };
    Stream.prototype.read = function(buffer, bufOffset, length) {
      var bytesRead = 0;
      while (bytesRead < length) {
        var c = this.readByte();
        if (c < 0) {
          return bytesRead === 0 ? -1 : bytesRead;
        }
        buffer[bufOffset++] = c;
        bytesRead++;
      }
      return bytesRead;
    };
    Stream.prototype.seek = function(new_pos) {
      throw new Error("abstract method seek() not implemented");
    };
    Stream.prototype.writeByte = function(_byte) {
      throw new Error("abstract method readByte() not implemented");
    };
    Stream.prototype.write = function(buffer, bufOffset, length) {
      var i;
      for (i = 0; i < length; i++) {
        this.writeByte(buffer[bufOffset++]);
      }
      return length;
    };
    Stream.prototype.flush = function() {
    };
    module.exports = Stream;
  }
});

// node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/crc32.js
var require_crc32 = __commonJS({
  "node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/crc32.js"(exports, module) {
    module.exports = (function() {
      var crc32Lookup = new Uint32Array([
        0,
        79764919,
        159529838,
        222504665,
        319059676,
        398814059,
        445009330,
        507990021,
        638119352,
        583659535,
        797628118,
        726387553,
        890018660,
        835552979,
        1015980042,
        944750013,
        1276238704,
        1221641927,
        1167319070,
        1095957929,
        1595256236,
        1540665371,
        1452775106,
        1381403509,
        1780037320,
        1859660671,
        1671105958,
        1733955601,
        2031960084,
        2111593891,
        1889500026,
        1952343757,
        2552477408,
        2632100695,
        2443283854,
        2506133561,
        2334638140,
        2414271883,
        2191915858,
        2254759653,
        3190512472,
        3135915759,
        3081330742,
        3009969537,
        2905550212,
        2850959411,
        2762807018,
        2691435357,
        3560074640,
        3505614887,
        3719321342,
        3648080713,
        3342211916,
        3287746299,
        3467911202,
        3396681109,
        4063920168,
        4143685023,
        4223187782,
        4286162673,
        3779000052,
        3858754371,
        3904687514,
        3967668269,
        881225847,
        809987520,
        1023691545,
        969234094,
        662832811,
        591600412,
        771767749,
        717299826,
        311336399,
        374308984,
        453813921,
        533576470,
        25881363,
        88864420,
        134795389,
        214552010,
        2023205639,
        2086057648,
        1897238633,
        1976864222,
        1804852699,
        1867694188,
        1645340341,
        1724971778,
        1587496639,
        1516133128,
        1461550545,
        1406951526,
        1302016099,
        1230646740,
        1142491917,
        1087903418,
        2896545431,
        2825181984,
        2770861561,
        2716262478,
        3215044683,
        3143675388,
        3055782693,
        3001194130,
        2326604591,
        2389456536,
        2200899649,
        2280525302,
        2578013683,
        2640855108,
        2418763421,
        2498394922,
        3769900519,
        3832873040,
        3912640137,
        3992402750,
        4088425275,
        4151408268,
        4197601365,
        4277358050,
        3334271071,
        3263032808,
        3476998961,
        3422541446,
        3585640067,
        3514407732,
        3694837229,
        3640369242,
        1762451694,
        1842216281,
        1619975040,
        1682949687,
        2047383090,
        2127137669,
        1938468188,
        2001449195,
        1325665622,
        1271206113,
        1183200824,
        1111960463,
        1543535498,
        1489069629,
        1434599652,
        1363369299,
        622672798,
        568075817,
        748617968,
        677256519,
        907627842,
        853037301,
        1067152940,
        995781531,
        51762726,
        131386257,
        177728840,
        240578815,
        269590778,
        349224269,
        429104020,
        491947555,
        4046411278,
        4126034873,
        4172115296,
        4234965207,
        3794477266,
        3874110821,
        3953728444,
        4016571915,
        3609705398,
        3555108353,
        3735388376,
        3664026991,
        3290680682,
        3236090077,
        3449943556,
        3378572211,
        3174993278,
        3120533705,
        3032266256,
        2961025959,
        2923101090,
        2868635157,
        2813903052,
        2742672763,
        2604032198,
        2683796849,
        2461293480,
        2524268063,
        2284983834,
        2364738477,
        2175806836,
        2238787779,
        1569362073,
        1498123566,
        1409854455,
        1355396672,
        1317987909,
        1246755826,
        1192025387,
        1137557660,
        2072149281,
        2135122070,
        1912620623,
        1992383480,
        1753615357,
        1816598090,
        1627664531,
        1707420964,
        295390185,
        358241886,
        404320391,
        483945776,
        43990325,
        106832002,
        186451547,
        266083308,
        932423249,
        861060070,
        1041341759,
        986742920,
        613929101,
        542559546,
        756411363,
        701822548,
        3316196985,
        3244833742,
        3425377559,
        3370778784,
        3601682597,
        3530312978,
        3744426955,
        3689838204,
        3819031489,
        3881883254,
        3928223919,
        4007849240,
        4037393693,
        4100235434,
        4180117107,
        4259748804,
        2310601993,
        2373574846,
        2151335527,
        2231098320,
        2596047829,
        2659030626,
        2470359227,
        2550115596,
        2947551409,
        2876312838,
        2788305887,
        2733848168,
        3165939309,
        3094707162,
        3040238851,
        2985771188
      ]);
      var CRC32 = function() {
        var crc = 4294967295;
        this.getCRC = function() {
          return ~crc >>> 0;
        };
        this.updateCRC = function(value) {
          crc = crc << 8 ^ crc32Lookup[(crc >>> 24 ^ value) & 255];
        };
        this.updateCRCRun = function(value, count) {
          while (count-- > 0) {
            crc = crc << 8 ^ crc32Lookup[(crc >>> 24 ^ value) & 255];
          }
        };
      };
      return CRC32;
    })();
  }
});

// node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/package.json
var require_package = __commonJS({
  "node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/package.json"(exports, module) {
    module.exports = {
      name: "seek-bzip",
      version: "2.0.0",
      contributors: [
        "C. Scott Ananian (http://cscott.net)",
        "Eli Skeggs",
        "Kevin Kwok",
        "Rob Landley (http://landley.net)"
      ],
      description: "a pure-JavaScript Node.JS module for random-access decoding bzip2 data",
      main: "./lib/index.js",
      repository: {
        type: "git",
        url: "https://github.com/cscott/seek-bzip.git"
      },
      license: "MIT",
      bin: {
        "seek-bunzip": "./bin/seek-bunzip",
        "seek-table": "./bin/seek-bzip-table"
      },
      directories: {
        test: "test"
      },
      dependencies: {
        commander: "^6.0.0"
      },
      devDependencies: {
        fibers: "^5.0.0",
        mocha: "^8.1.0"
      },
      scripts: {
        test: "mocha"
      }
    };
  }
});

// node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/index.js
var require_lib = __commonJS({
  "node_modules/.pnpm/seek-bzip@2.0.0/node_modules/seek-bzip/lib/index.js"(exports, module) {
    var BitReader = require_bitreader();
    var Stream = require_stream();
    var CRC32 = require_crc32();
    var pjson = require_package();
    var MAX_HUFCODE_BITS = 20;
    var MAX_SYMBOLS = 258;
    var SYMBOL_RUNA = 0;
    var SYMBOL_RUNB = 1;
    var MIN_GROUPS = 2;
    var MAX_GROUPS = 6;
    var GROUP_SIZE = 50;
    var WHOLEPI = "314159265359";
    var SQRTPI = "177245385090";
    var mtf = function(array, index) {
      var src = array[index], i;
      for (i = index; i > 0; i--) {
        array[i] = array[i - 1];
      }
      array[0] = src;
      return src;
    };
    var Err = {
      OK: 0,
      LAST_BLOCK: -1,
      NOT_BZIP_DATA: -2,
      UNEXPECTED_INPUT_EOF: -3,
      UNEXPECTED_OUTPUT_EOF: -4,
      DATA_ERROR: -5,
      OUT_OF_MEMORY: -6,
      OBSOLETE_INPUT: -7,
      END_OF_BLOCK: -8
    };
    var ErrorMessages = {};
    ErrorMessages[Err.LAST_BLOCK] = "Bad file checksum";
    ErrorMessages[Err.NOT_BZIP_DATA] = "Not bzip data";
    ErrorMessages[Err.UNEXPECTED_INPUT_EOF] = "Unexpected input EOF";
    ErrorMessages[Err.UNEXPECTED_OUTPUT_EOF] = "Unexpected output EOF";
    ErrorMessages[Err.DATA_ERROR] = "Data error";
    ErrorMessages[Err.OUT_OF_MEMORY] = "Out of memory";
    ErrorMessages[Err.OBSOLETE_INPUT] = "Obsolete (pre 0.9.5) bzip format not supported.";
    var _throw = function(status, optDetail) {
      var msg = ErrorMessages[status] || "unknown error";
      if (optDetail) {
        msg += ": " + optDetail;
      }
      var e = new TypeError(msg);
      e.errorCode = status;
      throw e;
    };
    var Bunzip = function(inputStream, outputStream) {
      this.writePos = this.writeCurrent = this.writeCount = 0;
      this._start_bunzip(inputStream, outputStream);
    };
    Bunzip.prototype._init_block = function() {
      var moreBlocks = this._get_next_block();
      if (!moreBlocks) {
        this.writeCount = -1;
        return false;
      }
      this.blockCRC = new CRC32();
      return true;
    };
    Bunzip.prototype._start_bunzip = function(inputStream, outputStream) {
      var buf = new Buffer(4);
      if (inputStream.read(buf, 0, 4) !== 4 || String.fromCharCode(buf[0], buf[1], buf[2]) !== "BZh")
        _throw(Err.NOT_BZIP_DATA, "bad magic");
      var level = buf[3] - 48;
      if (level < 1 || level > 9)
        _throw(Err.NOT_BZIP_DATA, "level out of range");
      this.reader = new BitReader(inputStream);
      this.dbufSize = 1e5 * level;
      this.nextoutput = 0;
      this.outputStream = outputStream;
      this.streamCRC = 0;
    };
    Bunzip.prototype._get_next_block = function() {
      var i, j, k;
      var reader = this.reader;
      var h = reader.pi();
      if (h === SQRTPI) {
        return false;
      }
      if (h !== WHOLEPI)
        _throw(Err.NOT_BZIP_DATA);
      this.targetBlockCRC = reader.read(32) >>> 0;
      this.streamCRC = (this.targetBlockCRC ^ (this.streamCRC << 1 | this.streamCRC >>> 31)) >>> 0;
      if (reader.read(1))
        _throw(Err.OBSOLETE_INPUT);
      var origPointer = reader.read(24);
      if (origPointer > this.dbufSize)
        _throw(Err.DATA_ERROR, "initial position out of bounds");
      var t = reader.read(16);
      var symToByte = new Buffer(256), symTotal = 0;
      for (i = 0; i < 16; i++) {
        if (t & 1 << 15 - i) {
          var o = i * 16;
          k = reader.read(16);
          for (j = 0; j < 16; j++)
            if (k & 1 << 15 - j)
              symToByte[symTotal++] = o + j;
        }
      }
      var groupCount = reader.read(3);
      if (groupCount < MIN_GROUPS || groupCount > MAX_GROUPS)
        _throw(Err.DATA_ERROR);
      var nSelectors = reader.read(15);
      if (nSelectors === 0)
        _throw(Err.DATA_ERROR);
      var mtfSymbol = new Buffer(256);
      for (i = 0; i < groupCount; i++)
        mtfSymbol[i] = i;
      var selectors = new Buffer(nSelectors);
      for (i = 0; i < nSelectors; i++) {
        for (j = 0; reader.read(1); j++)
          if (j >= groupCount) _throw(Err.DATA_ERROR);
        selectors[i] = mtf(mtfSymbol, j);
      }
      var symCount = symTotal + 2;
      var groups = [], hufGroup;
      for (j = 0; j < groupCount; j++) {
        var length = new Buffer(symCount), temp = new Uint16Array(MAX_HUFCODE_BITS + 1);
        t = reader.read(5);
        for (i = 0; i < symCount; i++) {
          for (; ; ) {
            if (t < 1 || t > MAX_HUFCODE_BITS) _throw(Err.DATA_ERROR);
            if (!reader.read(1))
              break;
            if (!reader.read(1))
              t++;
            else
              t--;
          }
          length[i] = t;
        }
        var minLen, maxLen;
        minLen = maxLen = length[0];
        for (i = 1; i < symCount; i++) {
          if (length[i] > maxLen)
            maxLen = length[i];
          else if (length[i] < minLen)
            minLen = length[i];
        }
        hufGroup = {};
        groups.push(hufGroup);
        hufGroup.permute = new Uint16Array(MAX_SYMBOLS);
        hufGroup.limit = new Uint32Array(MAX_HUFCODE_BITS + 2);
        hufGroup.base = new Uint32Array(MAX_HUFCODE_BITS + 1);
        hufGroup.minLen = minLen;
        hufGroup.maxLen = maxLen;
        var pp = 0;
        for (i = minLen; i <= maxLen; i++) {
          temp[i] = hufGroup.limit[i] = 0;
          for (t = 0; t < symCount; t++)
            if (length[t] === i)
              hufGroup.permute[pp++] = t;
        }
        for (i = 0; i < symCount; i++)
          temp[length[i]]++;
        pp = t = 0;
        for (i = minLen; i < maxLen; i++) {
          pp += temp[i];
          hufGroup.limit[i] = pp - 1;
          pp <<= 1;
          t += temp[i];
          hufGroup.base[i + 1] = pp - t;
        }
        hufGroup.limit[maxLen + 1] = Number.MAX_VALUE;
        hufGroup.limit[maxLen] = pp + temp[maxLen] - 1;
        hufGroup.base[minLen] = 0;
      }
      var byteCount = new Uint32Array(256);
      for (i = 0; i < 256; i++)
        mtfSymbol[i] = i;
      var runPos = 0, dbufCount = 0, selector = 0, uc;
      var dbuf = this.dbuf = new Uint32Array(this.dbufSize);
      symCount = 0;
      for (; ; ) {
        if (!symCount--) {
          symCount = GROUP_SIZE - 1;
          if (selector >= nSelectors) {
            _throw(Err.DATA_ERROR);
          }
          hufGroup = groups[selectors[selector++]];
        }
        i = hufGroup.minLen;
        j = reader.read(i);
        for (; ; i++) {
          if (i > hufGroup.maxLen) {
            _throw(Err.DATA_ERROR);
          }
          if (j <= hufGroup.limit[i])
            break;
          j = j << 1 | reader.read(1);
        }
        j -= hufGroup.base[i];
        if (j < 0 || j >= MAX_SYMBOLS) {
          _throw(Err.DATA_ERROR);
        }
        var nextSym = hufGroup.permute[j];
        if (nextSym === SYMBOL_RUNA || nextSym === SYMBOL_RUNB) {
          if (!runPos) {
            runPos = 1;
            t = 0;
          }
          if (nextSym === SYMBOL_RUNA)
            t += runPos;
          else
            t += 2 * runPos;
          runPos <<= 1;
          continue;
        }
        if (runPos) {
          runPos = 0;
          if (dbufCount + t > this.dbufSize) {
            _throw(Err.DATA_ERROR);
          }
          uc = symToByte[mtfSymbol[0]];
          byteCount[uc] += t;
          while (t--)
            dbuf[dbufCount++] = uc;
        }
        if (nextSym > symTotal)
          break;
        if (dbufCount >= this.dbufSize) {
          _throw(Err.DATA_ERROR);
        }
        i = nextSym - 1;
        uc = mtf(mtfSymbol, i);
        uc = symToByte[uc];
        byteCount[uc]++;
        dbuf[dbufCount++] = uc;
      }
      if (origPointer < 0 || origPointer >= dbufCount) {
        _throw(Err.DATA_ERROR);
      }
      j = 0;
      for (i = 0; i < 256; i++) {
        k = j + byteCount[i];
        byteCount[i] = j;
        j = k;
      }
      for (i = 0; i < dbufCount; i++) {
        uc = dbuf[i] & 255;
        dbuf[byteCount[uc]] |= i << 8;
        byteCount[uc]++;
      }
      var pos = 0, current = 0, run = 0;
      if (dbufCount) {
        pos = dbuf[origPointer];
        current = pos & 255;
        pos >>= 8;
        run = -1;
      }
      this.writePos = pos;
      this.writeCurrent = current;
      this.writeCount = dbufCount;
      this.writeRun = run;
      return true;
    };
    Bunzip.prototype._read_bunzip = function(outputBuffer, len) {
      var copies, previous, outbyte;
      if (this.writeCount < 0) {
        return 0;
      }
      var gotcount = 0;
      var dbuf = this.dbuf, pos = this.writePos, current = this.writeCurrent;
      var dbufCount = this.writeCount, outputsize = this.outputsize;
      var run = this.writeRun;
      while (dbufCount) {
        dbufCount--;
        previous = current;
        pos = dbuf[pos];
        current = pos & 255;
        pos >>= 8;
        if (run++ === 3) {
          copies = current;
          outbyte = previous;
          current = -1;
        } else {
          copies = 1;
          outbyte = current;
        }
        this.blockCRC.updateCRCRun(outbyte, copies);
        while (copies--) {
          this.outputStream.writeByte(outbyte);
          this.nextoutput++;
        }
        if (current != previous)
          run = 0;
      }
      this.writeCount = dbufCount;
      if (this.blockCRC.getCRC() !== this.targetBlockCRC) {
        _throw(Err.DATA_ERROR, "Bad block CRC (got " + this.blockCRC.getCRC().toString(16) + " expected " + this.targetBlockCRC.toString(16) + ")");
      }
      return this.nextoutput;
    };
    var coerceInputStream = function(input) {
      if ("readByte" in input) {
        return input;
      }
      var inputStream = new Stream();
      inputStream.pos = 0;
      inputStream.readByte = function() {
        return input[this.pos++];
      };
      inputStream.seek = function(pos) {
        this.pos = pos;
      };
      inputStream.eof = function() {
        return this.pos >= input.length;
      };
      return inputStream;
    };
    var coerceOutputStream = function(output) {
      var outputStream = new Stream();
      var resizeOk = true;
      if (output) {
        if (typeof output === "number") {
          outputStream.buffer = new Buffer(output);
          resizeOk = false;
        } else if ("writeByte" in output) {
          return output;
        } else {
          outputStream.buffer = output;
          resizeOk = false;
        }
      } else {
        outputStream.buffer = new Buffer(16384);
      }
      outputStream.pos = 0;
      outputStream.writeByte = function(_byte) {
        if (resizeOk && this.pos >= this.buffer.length) {
          var newBuffer = new Buffer(this.buffer.length * 2);
          this.buffer.copy(newBuffer);
          this.buffer = newBuffer;
        }
        this.buffer[this.pos++] = _byte;
      };
      outputStream.getBuffer = function() {
        if (this.pos !== this.buffer.length) {
          if (!resizeOk)
            throw new TypeError("outputsize does not match decoded input");
          var newBuffer = new Buffer(this.pos);
          this.buffer.copy(newBuffer, 0, 0, this.pos);
          this.buffer = newBuffer;
        }
        return this.buffer;
      };
      outputStream._coerced = true;
      return outputStream;
    };
    Bunzip.Err = Err;
    Bunzip.decode = function(input, output, multistream) {
      var inputStream = coerceInputStream(input);
      var outputStream = coerceOutputStream(output);
      var bz = new Bunzip(inputStream, outputStream);
      while (true) {
        if ("eof" in inputStream && inputStream.eof()) break;
        if (bz._init_block()) {
          bz._read_bunzip();
        } else {
          var targetStreamCRC = bz.reader.read(32) >>> 0;
          if (targetStreamCRC !== bz.streamCRC) {
            _throw(Err.DATA_ERROR, "Bad stream CRC (got " + bz.streamCRC.toString(16) + " expected " + targetStreamCRC.toString(16) + ")");
          }
          if (multistream && "eof" in inputStream && !inputStream.eof()) {
            bz._start_bunzip(inputStream, outputStream);
          } else break;
        }
      }
      if ("getBuffer" in outputStream)
        return outputStream.getBuffer();
    };
    Bunzip.decodeBlock = function(input, pos, output) {
      var inputStream = coerceInputStream(input);
      var outputStream = coerceOutputStream(output);
      var bz = new Bunzip(inputStream, outputStream);
      bz.reader.seek(pos);
      var moreBlocks = bz._get_next_block();
      if (moreBlocks) {
        bz.blockCRC = new CRC32();
        bz.writeCopies = 0;
        bz._read_bunzip();
      }
      if ("getBuffer" in outputStream)
        return outputStream.getBuffer();
    };
    Bunzip.table = function(input, callback, multistream) {
      var inputStream = new Stream();
      inputStream.delegate = coerceInputStream(input);
      inputStream.pos = 0;
      inputStream.readByte = function() {
        this.pos++;
        return this.delegate.readByte();
      };
      if (inputStream.delegate.eof) {
        inputStream.eof = inputStream.delegate.eof.bind(inputStream.delegate);
      }
      var outputStream = new Stream();
      outputStream.pos = 0;
      outputStream.writeByte = function() {
        this.pos++;
      };
      var bz = new Bunzip(inputStream, outputStream);
      var blockSize = bz.dbufSize;
      while (true) {
        if ("eof" in inputStream && inputStream.eof()) break;
        var position = inputStream.pos * 8 + bz.reader.bitOffset;
        if (bz.reader.hasByte) {
          position -= 8;
        }
        if (bz._init_block()) {
          var start = outputStream.pos;
          bz._read_bunzip();
          callback(position, outputStream.pos - start);
        } else {
          var crc = bz.reader.read(32);
          if (multistream && "eof" in inputStream && !inputStream.eof()) {
            bz._start_bunzip(inputStream, outputStream);
            console.assert(
              bz.dbufSize === blockSize,
              "shouldn't change block size within multistream file"
            );
          } else break;
        }
      }
    };
    Bunzip.Stream = Stream;
    Bunzip.version = pjson.version;
    Bunzip.license = pjson.license;
    module.exports = Bunzip;
  }
});

// node_modules/.pnpm/modern-tar@0.7.3/node_modules/modern-tar/dist/unpacker-BpPBxY8N.js
var BLOCK_SIZE = 512;
var BLOCK_SIZE_MASK = 511;
var DEFAULT_FILE_MODE = 420;
var DEFAULT_DIR_MODE = 493;
var USTAR_NAME_OFFSET = 0;
var USTAR_NAME_SIZE = 100;
var USTAR_MODE_OFFSET = 100;
var USTAR_MODE_SIZE = 8;
var USTAR_UID_OFFSET = 108;
var USTAR_UID_SIZE = 8;
var USTAR_GID_OFFSET = 116;
var USTAR_GID_SIZE = 8;
var USTAR_SIZE_OFFSET = 124;
var USTAR_SIZE_SIZE = 12;
var USTAR_MTIME_OFFSET = 136;
var USTAR_MTIME_SIZE = 12;
var USTAR_CHECKSUM_OFFSET = 148;
var USTAR_CHECKSUM_SIZE = 8;
var USTAR_TYPEFLAG_OFFSET = 156;
var USTAR_TYPEFLAG_SIZE = 1;
var USTAR_LINKNAME_OFFSET = 157;
var USTAR_LINKNAME_SIZE = 100;
var USTAR_MAGIC_OFFSET = 257;
var USTAR_MAGIC_SIZE = 6;
var USTAR_VERSION_OFFSET = 263;
var USTAR_VERSION_SIZE = 2;
var USTAR_UNAME_OFFSET = 265;
var USTAR_UNAME_SIZE = 32;
var USTAR_GNAME_OFFSET = 297;
var USTAR_GNAME_SIZE = 32;
var USTAR_PREFIX_OFFSET = 345;
var USTAR_PREFIX_SIZE = 155;
var USTAR_VERSION = "00";
var USTAR_MAX_UID_GID = 2097151;
var USTAR_MAX_SIZE = 8589934591;
var FILE = "file";
var LINK = "link";
var SYMLINK = "symlink";
var DIRECTORY = "directory";
var TYPEFLAG = {
  file: "0",
  link: "1",
  symlink: "2",
  "character-device": "3",
  "block-device": "4",
  directory: "5",
  fifo: "6",
  "pax-header": "x",
  "pax-global-header": "g",
  "gnu-long-name": "L",
  "gnu-long-link-name": "K"
};
var FLAGTYPE = {
  "0": FILE,
  "1": LINK,
  "2": SYMLINK,
  "3": "character-device",
  "4": "block-device",
  "5": DIRECTORY,
  "6": "fifo",
  x: "pax-header",
  g: "pax-global-header",
  L: "gnu-long-name",
  K: "gnu-long-link-name"
};
var ZERO_BLOCK = new Uint8Array(BLOCK_SIZE);
var EMPTY = new Uint8Array(0);
var encoder = new TextEncoder();
var decoder = new TextDecoder();
function writeString(view, offset, size, value) {
  if (value) encoder.encodeInto(value, view.subarray(offset, offset + size));
}
function writeOctal(view, offset, size, value) {
  if (value === void 0) return;
  const octalString = value.toString(8).padStart(size - 1, "0");
  encoder.encodeInto(octalString, view.subarray(offset, offset + size - 1));
}
function readString(view, offset, size) {
  const end = view.indexOf(0, offset);
  const sliceEnd = end === -1 || end > offset + size ? offset + size : end;
  return decoder.decode(view.subarray(offset, sliceEnd));
}
function readOctal(view, offset, size) {
  let value = 0;
  const end = offset + size;
  for (let i = offset; i < end; i++) {
    const charCode = view[i];
    if (charCode === 0) break;
    if (charCode === 32) continue;
    value = value * 8 + (charCode - 48);
  }
  return value;
}
function readNumeric(view, offset, size) {
  if (view[offset] & 128) {
    let result = 0;
    result = view[offset] & 127;
    for (let i = 1; i < size; i++) result = result * 256 + view[offset + i];
    if (!Number.isSafeInteger(result)) throw new Error("TAR number too large");
    return result;
  }
  return readOctal(view, offset, size);
}
var isBodyless = (header) => header.type === DIRECTORY || header.type === SYMLINK || header.type === LINK;
async function normalizeBody(body) {
  if (body === null || body === void 0) return EMPTY;
  if (body instanceof Uint8Array) return body;
  if (typeof body === "string") return encoder.encode(body);
  if (body instanceof ArrayBuffer) return new Uint8Array(body);
  if (body instanceof Blob) return new Uint8Array(await body.arrayBuffer());
  throw new TypeError("Unsupported content type for entry body.");
}
function transformHeader(header, options) {
  const { strip, filter, map } = options;
  if (!strip && !filter && !map) return header;
  const h = { ...header };
  if (strip && strip > 0) {
    const components = h.name.split("/").filter(Boolean);
    if (strip >= components.length) return null;
    const newName = components.slice(strip).join("/");
    h.name = h.type === DIRECTORY && !newName.endsWith("/") ? `${newName}/` : newName;
    if (h.linkname?.startsWith("/")) {
      const linkComponents = h.linkname.split("/").filter(Boolean);
      h.linkname = strip >= linkComponents.length ? "/" : `/${linkComponents.slice(strip).join("/")}`;
    }
  }
  if (filter?.(h) === false) return null;
  const result = map ? map(h) : h;
  if (result && (!result.name || !result.name.trim() || result.name === "." || result.name === "/")) return null;
  return result;
}
var CHECKSUM_SPACE = 32;
var ASCII_ZERO = 48;
function validateChecksum(block) {
  const stored = readOctal(block, USTAR_CHECKSUM_OFFSET, USTAR_CHECKSUM_SIZE);
  let sum = 0;
  for (let i = 0; i < block.length; i++) if (i >= USTAR_CHECKSUM_OFFSET && i < USTAR_CHECKSUM_OFFSET + USTAR_CHECKSUM_SIZE) sum += CHECKSUM_SPACE;
  else sum += block[i];
  return stored === sum;
}
function writeChecksum(block) {
  block.fill(CHECKSUM_SPACE, USTAR_CHECKSUM_OFFSET, USTAR_CHECKSUM_OFFSET + USTAR_CHECKSUM_SIZE);
  let checksum = 0;
  for (const byte of block) checksum += byte;
  for (let i = USTAR_CHECKSUM_OFFSET + 6 - 1; i >= USTAR_CHECKSUM_OFFSET; i--) {
    block[i] = (checksum & 7) + ASCII_ZERO;
    checksum >>= 3;
  }
  block[USTAR_CHECKSUM_OFFSET + 6] = 0;
  block[USTAR_CHECKSUM_OFFSET + 7] = CHECKSUM_SPACE;
}
function generatePax(header) {
  const paxRecords = {};
  if (header.name.length > USTAR_NAME_SIZE) {
    if (findUstarSplit(header.name) === null) paxRecords.path = header.name;
  }
  if (header.linkname && header.linkname.length > USTAR_NAME_SIZE) paxRecords.linkpath = header.linkname;
  if (header.uname && header.uname.length > USTAR_UNAME_SIZE) paxRecords.uname = header.uname;
  if (header.gname && header.gname.length > USTAR_GNAME_SIZE) paxRecords.gname = header.gname;
  if (header.uid != null && header.uid > USTAR_MAX_UID_GID) paxRecords.uid = String(header.uid);
  if (header.gid != null && header.gid > USTAR_MAX_UID_GID) paxRecords.gid = String(header.gid);
  if (header.size != null && header.size > USTAR_MAX_SIZE) paxRecords.size = String(header.size);
  if (header.pax) Object.assign(paxRecords, header.pax);
  const paxEntries = Object.entries(paxRecords);
  if (paxEntries.length === 0) return null;
  const paxBody = encoder.encode(paxEntries.map(([key, value]) => {
    const record = `${key}=${value}
`;
    const partLength = encoder.encode(record).length + 1;
    let totalLength = partLength + String(partLength).length;
    totalLength = partLength + String(totalLength).length;
    return `${totalLength} ${record}`;
  }).join(""));
  return {
    paxHeader: createTarHeader({
      name: decoder.decode(encoder.encode(`PaxHeader/${header.name}`).slice(0, 100)),
      size: paxBody.length,
      type: "pax-header",
      mode: 420,
      mtime: header.mtime,
      uname: header.uname,
      gname: header.gname,
      uid: header.uid,
      gid: header.gid
    }),
    paxBody
  };
}
function findUstarSplit(path) {
  if (path.length <= USTAR_NAME_SIZE) return null;
  const minSlashIndex = path.length - USTAR_NAME_SIZE - 1;
  const slashIndex = path.lastIndexOf("/", USTAR_PREFIX_SIZE);
  if (slashIndex > 0 && slashIndex >= minSlashIndex) return {
    prefix: path.slice(0, slashIndex),
    name: path.slice(slashIndex + 1)
  };
  return null;
}
function createTarHeader(header) {
  const view = new Uint8Array(BLOCK_SIZE);
  const size = isBodyless(header) ? 0 : header.size ?? 0;
  let name = header.name;
  let prefix = "";
  if (!header.pax?.path) {
    const split = findUstarSplit(name);
    if (split) {
      name = split.name;
      prefix = split.prefix;
    }
  }
  writeString(view, USTAR_NAME_OFFSET, USTAR_NAME_SIZE, name);
  writeOctal(view, USTAR_MODE_OFFSET, USTAR_MODE_SIZE, header.mode ?? (header.type === DIRECTORY ? DEFAULT_DIR_MODE : DEFAULT_FILE_MODE));
  writeOctal(view, USTAR_UID_OFFSET, USTAR_UID_SIZE, header.uid ?? 0);
  writeOctal(view, USTAR_GID_OFFSET, USTAR_GID_SIZE, header.gid ?? 0);
  writeOctal(view, USTAR_SIZE_OFFSET, USTAR_SIZE_SIZE, size);
  writeOctal(view, USTAR_MTIME_OFFSET, USTAR_MTIME_SIZE, Math.floor((header.mtime?.getTime() ?? Date.now()) / 1e3));
  writeString(view, USTAR_TYPEFLAG_OFFSET, USTAR_TYPEFLAG_SIZE, TYPEFLAG[header.type ?? FILE]);
  writeString(view, USTAR_LINKNAME_OFFSET, USTAR_LINKNAME_SIZE, header.linkname);
  writeString(view, USTAR_MAGIC_OFFSET, USTAR_MAGIC_SIZE, "ustar\0");
  writeString(view, USTAR_VERSION_OFFSET, USTAR_VERSION_SIZE, USTAR_VERSION);
  writeString(view, USTAR_UNAME_OFFSET, USTAR_UNAME_SIZE, header.uname);
  writeString(view, USTAR_GNAME_OFFSET, USTAR_GNAME_SIZE, header.gname);
  writeString(view, USTAR_PREFIX_OFFSET, USTAR_PREFIX_SIZE, prefix);
  writeChecksum(view);
  return view;
}
function parseUstarHeader(block, strict) {
  if (strict && !validateChecksum(block)) throw new Error("Invalid tar header checksum.");
  const typeflag = readString(block, USTAR_TYPEFLAG_OFFSET, USTAR_TYPEFLAG_SIZE);
  const header = {
    name: readString(block, USTAR_NAME_OFFSET, USTAR_NAME_SIZE),
    mode: readOctal(block, USTAR_MODE_OFFSET, USTAR_MODE_SIZE),
    uid: readNumeric(block, USTAR_UID_OFFSET, USTAR_UID_SIZE),
    gid: readNumeric(block, USTAR_GID_OFFSET, USTAR_GID_SIZE),
    size: readNumeric(block, USTAR_SIZE_OFFSET, USTAR_SIZE_SIZE),
    mtime: /* @__PURE__ */ new Date(readNumeric(block, USTAR_MTIME_OFFSET, USTAR_MTIME_SIZE) * 1e3),
    type: FLAGTYPE[typeflag] || FILE,
    linkname: readString(block, USTAR_LINKNAME_OFFSET, USTAR_LINKNAME_SIZE)
  };
  const magic = readString(block, USTAR_MAGIC_OFFSET, USTAR_MAGIC_SIZE);
  if (magic.trim() === "ustar") {
    header.uname = readString(block, USTAR_UNAME_OFFSET, USTAR_UNAME_SIZE);
    header.gname = readString(block, USTAR_GNAME_OFFSET, USTAR_GNAME_SIZE);
  }
  if (magic === "ustar") header.prefix = readString(block, USTAR_PREFIX_OFFSET, USTAR_PREFIX_SIZE);
  return header;
}
var PAX_MAPPING = {
  path: ["name", (v) => v],
  linkpath: ["linkname", (v) => v],
  size: ["size", (v) => parseInt(v, 10)],
  mtime: ["mtime", parseFloat],
  uid: ["uid", (v) => parseInt(v, 10)],
  gid: ["gid", (v) => parseInt(v, 10)],
  uname: ["uname", (v) => v],
  gname: ["gname", (v) => v]
};
function parsePax(buffer) {
  const decoder$1 = new TextDecoder("utf-8");
  const overrides = {};
  const pax = {};
  let offset = 0;
  while (offset < buffer.length) {
    const spaceIndex = buffer.indexOf(32, offset);
    if (spaceIndex === -1) break;
    const length = parseInt(decoder$1.decode(buffer.subarray(offset, spaceIndex)), 10);
    if (Number.isNaN(length) || length === 0) break;
    const recordEnd = offset + length;
    const [key, value] = decoder$1.decode(buffer.subarray(spaceIndex + 1, recordEnd - 1)).split("=", 2);
    if (key && value !== void 0) {
      pax[key] = value;
      const mapping = PAX_MAPPING[key];
      if (mapping) {
        const [targetKey, parser] = mapping;
        const parsedValue = parser(value);
        if (typeof parsedValue === "string" || !Number.isNaN(parsedValue)) overrides[targetKey] = parsedValue;
      }
    }
    offset = recordEnd;
  }
  if (Object.keys(pax).length > 0) overrides.pax = pax;
  return overrides;
}
function applyOverrides(header, overrides) {
  if (overrides.name !== void 0) header.name = overrides.name;
  if (overrides.linkname !== void 0) header.linkname = overrides.linkname;
  if (overrides.size !== void 0) header.size = overrides.size;
  if (overrides.mtime !== void 0) header.mtime = /* @__PURE__ */ new Date(overrides.mtime * 1e3);
  if (overrides.uid !== void 0) header.uid = overrides.uid;
  if (overrides.gid !== void 0) header.gid = overrides.gid;
  if (overrides.uname !== void 0) header.uname = overrides.uname;
  if (overrides.gname !== void 0) header.gname = overrides.gname;
  if (overrides.pax) header.pax = Object.assign({}, header.pax ?? {}, overrides.pax);
}
function getMetaParser(type) {
  switch (type) {
    case "pax-global-header":
    case "pax-header":
      return parsePax;
    case "gnu-long-name":
      return (data) => ({ name: readString(data, 0, data.length) });
    case "gnu-long-link-name":
      return (data) => ({ linkname: readString(data, 0, data.length) });
    default:
      return;
  }
}
function getHeaderBlocks(header) {
  const base = createTarHeader(header);
  const pax = generatePax(header);
  if (!pax) return [base];
  const paxPadding = -pax.paxBody.length & BLOCK_SIZE_MASK;
  const paddingBlocks = paxPadding > 0 ? [ZERO_BLOCK.subarray(0, paxPadding)] : [];
  return [
    pax.paxHeader,
    pax.paxBody,
    ...paddingBlocks,
    base
  ];
}
var EOF_BUFFER = new Uint8Array(BLOCK_SIZE * 2);
function createTarPacker(onData, onError, onFinalize) {
  let currentHeader = null;
  let bytesWritten = 0;
  let finalized = false;
  return {
    add(header) {
      if (finalized) {
        const error = /* @__PURE__ */ new Error("No new tar entries after finalize.");
        onError(error);
        throw error;
      }
      if (currentHeader !== null) {
        const error = /* @__PURE__ */ new Error("Previous entry must be completed before adding a new one");
        onError(error);
        throw error;
      }
      try {
        const size = isBodyless(header) ? 0 : header.size ?? 0;
        const headerBlocks = getHeaderBlocks({
          ...header,
          size
        });
        for (const block of headerBlocks) onData(block);
        currentHeader = {
          ...header,
          size
        };
        bytesWritten = 0;
      } catch (error) {
        onError(error);
      }
    },
    write(chunk) {
      if (!currentHeader) {
        const error = /* @__PURE__ */ new Error("No active tar entry.");
        onError(error);
        throw error;
      }
      if (finalized) {
        const error = /* @__PURE__ */ new Error("Cannot write data after finalize.");
        onError(error);
        throw error;
      }
      const newTotal = bytesWritten + chunk.length;
      if (newTotal > currentHeader.size) {
        const error = /* @__PURE__ */ new Error(`"${currentHeader.name}" exceeds given size of ${currentHeader.size} bytes.`);
        onError(error);
        throw error;
      }
      try {
        bytesWritten = newTotal;
        onData(chunk);
      } catch (error) {
        onError(error);
      }
    },
    endEntry() {
      if (!currentHeader) {
        const error = /* @__PURE__ */ new Error("No active entry to end.");
        onError(error);
        throw error;
      }
      if (finalized) {
        const error = /* @__PURE__ */ new Error("Cannot end entry after finalize.");
        onError(error);
        throw error;
      }
      try {
        if (bytesWritten !== currentHeader.size) {
          const error = /* @__PURE__ */ new Error(`Size mismatch for "${currentHeader.name}".`);
          onError(error);
          throw error;
        }
        const paddingSize = -currentHeader.size & BLOCK_SIZE_MASK;
        if (paddingSize > 0) onData(new Uint8Array(paddingSize));
        currentHeader = null;
        bytesWritten = 0;
      } catch (error) {
        onError(error);
        throw error;
      }
    },
    finalize() {
      if (finalized) {
        const error = /* @__PURE__ */ new Error("Archive has already been finalized");
        onError(error);
        throw error;
      }
      if (currentHeader !== null) {
        const error = /* @__PURE__ */ new Error("Cannot finalize while an entry is still active");
        onError(error);
        throw error;
      }
      try {
        onData(EOF_BUFFER);
        finalized = true;
        if (onFinalize) onFinalize();
      } catch (error) {
        onError(error);
      }
    }
  };
}
var INITIAL_CAPACITY = 256;
function createChunkQueue() {
  let chunks = new Array(INITIAL_CAPACITY);
  let capacityMask = chunks.length - 1;
  let head = 0;
  let tail = 0;
  let totalAvailable = 0;
  const consumeFromHead = (count) => {
    const chunk = chunks[head];
    if (count === chunk.length) {
      chunks[head] = EMPTY;
      head = head + 1 & capacityMask;
    } else chunks[head] = chunk.subarray(count);
    totalAvailable -= count;
    if (totalAvailable === 0 && chunks.length > INITIAL_CAPACITY) {
      chunks = new Array(INITIAL_CAPACITY);
      capacityMask = INITIAL_CAPACITY - 1;
      head = 0;
      tail = 0;
    }
  };
  function pull(bytes, callback) {
    if (callback) {
      let fed = 0;
      let remaining$1 = Math.min(bytes, totalAvailable);
      while (remaining$1 > 0) {
        const chunk = chunks[head];
        const toFeed = Math.min(remaining$1, chunk.length);
        const segment = toFeed === chunk.length ? chunk : chunk.subarray(0, toFeed);
        consumeFromHead(toFeed);
        remaining$1 -= toFeed;
        fed += toFeed;
        if (!callback(segment)) break;
      }
      return fed;
    }
    if (totalAvailable < bytes) return null;
    if (bytes === 0) return EMPTY;
    const firstChunk = chunks[head];
    if (firstChunk.length >= bytes) {
      const view = firstChunk.length === bytes ? firstChunk : firstChunk.subarray(0, bytes);
      consumeFromHead(bytes);
      return view;
    }
    const result = new Uint8Array(bytes);
    let copied = 0;
    let remaining = bytes;
    while (remaining > 0) {
      const chunk = chunks[head];
      const toCopy = Math.min(remaining, chunk.length);
      result.set(toCopy === chunk.length ? chunk : chunk.subarray(0, toCopy), copied);
      copied += toCopy;
      remaining -= toCopy;
      consumeFromHead(toCopy);
    }
    return result;
  }
  return {
    push: (chunk) => {
      if (chunk.length === 0) return;
      let nextTail = tail + 1 & capacityMask;
      if (nextTail === head) {
        const oldLen = chunks.length;
        const newLen = oldLen * 2;
        const newChunks = new Array(newLen);
        const count = tail - head + oldLen & oldLen - 1;
        if (head < tail) for (let i = 0; i < count; i++) newChunks[i] = chunks[head + i];
        else if (count > 0) {
          const firstPart = oldLen - head;
          for (let i = 0; i < firstPart; i++) newChunks[i] = chunks[head + i];
          for (let i = 0; i < tail; i++) newChunks[firstPart + i] = chunks[i];
        }
        chunks = newChunks;
        capacityMask = newLen - 1;
        head = 0;
        tail = count;
        nextTail = tail + 1 & capacityMask;
      }
      chunks[tail] = chunk;
      tail = nextTail;
      totalAvailable += chunk.length;
    },
    available: () => totalAvailable,
    peek: (bytes) => {
      if (totalAvailable < bytes) return null;
      if (bytes === 0) return EMPTY;
      const firstChunk = chunks[head];
      if (firstChunk.length >= bytes) return firstChunk.length === bytes ? firstChunk : firstChunk.subarray(0, bytes);
      const result = new Uint8Array(bytes);
      let copied = 0;
      let index = head;
      while (copied < bytes) {
        const chunk = chunks[index];
        const toCopy = Math.min(bytes - copied, chunk.length);
        if (toCopy === chunk.length) result.set(chunk, copied);
        else result.set(chunk.subarray(0, toCopy), copied);
        copied += toCopy;
        index = index + 1 & capacityMask;
      }
      return result;
    },
    discard: (bytes) => {
      if (bytes > totalAvailable) throw new Error("Too many bytes consumed");
      if (bytes === 0) return;
      let remaining = bytes;
      while (remaining > 0) {
        const chunk = chunks[head];
        const toConsume = Math.min(remaining, chunk.length);
        consumeFromHead(toConsume);
        remaining -= toConsume;
      }
    },
    pull
  };
}
var STATE_HEADER = 0;
var STATE_BODY = 1;
var truncateErr = /* @__PURE__ */ new Error("Tar archive is truncated.");
function createUnpacker(options = {}) {
  const strict = options.strict ?? false;
  const { available, peek, push, discard, pull } = createChunkQueue();
  let state = STATE_HEADER;
  let ended = false;
  let done = false;
  let eof = false;
  let currentEntry = null;
  const paxGlobals = {};
  let nextEntryOverrides = {};
  const unpacker = {
    isEntryActive: () => state === STATE_BODY,
    isBodyComplete: () => !currentEntry || currentEntry.remaining === 0,
    write(chunk) {
      if (ended) throw new Error("Archive already ended.");
      push(chunk);
    },
    end() {
      ended = true;
    },
    readHeader() {
      if (state !== STATE_HEADER) throw new Error("Cannot read header while an entry is active");
      if (done) return void 0;
      while (!done) {
        if (available() < BLOCK_SIZE) {
          if (ended) {
            if (available() > 0 && strict) throw truncateErr;
            done = true;
            return;
          }
          return null;
        }
        const headerBlock = peek(BLOCK_SIZE);
        if (isZeroBlock(headerBlock)) {
          if (available() < BLOCK_SIZE * 2) {
            if (ended) {
              if (strict) throw truncateErr;
              done = true;
              return;
            }
            return null;
          }
          if (isZeroBlock(peek(BLOCK_SIZE * 2).subarray(BLOCK_SIZE))) {
            discard(BLOCK_SIZE * 2);
            done = true;
            eof = true;
            return;
          }
          if (strict) throw new Error("Invalid tar header.");
          discard(BLOCK_SIZE);
          continue;
        }
        let internalHeader;
        try {
          internalHeader = parseUstarHeader(headerBlock, strict);
        } catch (err) {
          if (strict) throw err;
          discard(BLOCK_SIZE);
          continue;
        }
        const metaParser = getMetaParser(internalHeader.type);
        if (metaParser) {
          const paddedSize = internalHeader.size + BLOCK_SIZE_MASK & ~BLOCK_SIZE_MASK;
          if (available() < BLOCK_SIZE + paddedSize) {
            if (ended && strict) throw truncateErr;
            return null;
          }
          discard(BLOCK_SIZE);
          const overrides = metaParser(pull(paddedSize).subarray(0, internalHeader.size));
          const target = internalHeader.type === "pax-global-header" ? paxGlobals : nextEntryOverrides;
          for (const key in overrides) target[key] = overrides[key];
          continue;
        }
        discard(BLOCK_SIZE);
        const header = internalHeader;
        if (internalHeader.prefix) header.name = `${internalHeader.prefix}/${header.name}`;
        applyOverrides(header, paxGlobals);
        applyOverrides(header, nextEntryOverrides);
        nextEntryOverrides = {};
        currentEntry = {
          header,
          remaining: header.size,
          padding: -header.size & BLOCK_SIZE_MASK
        };
        state = STATE_BODY;
        return header;
      }
    },
    streamBody(callback) {
      if (state !== STATE_BODY || !currentEntry || currentEntry.remaining === 0) return 0;
      const bytesToFeed = Math.min(currentEntry.remaining, available());
      if (bytesToFeed === 0) return 0;
      const fed = pull(bytesToFeed, callback);
      currentEntry.remaining -= fed;
      return fed;
    },
    skipPadding() {
      if (state !== STATE_BODY || !currentEntry) return true;
      if (currentEntry.remaining > 0) throw new Error("Body not fully consumed");
      if (available() < currentEntry.padding) return false;
      discard(currentEntry.padding);
      currentEntry = null;
      state = STATE_HEADER;
      return true;
    },
    skipEntry() {
      if (state !== STATE_BODY || !currentEntry) return true;
      const toDiscard = Math.min(currentEntry.remaining, available());
      if (toDiscard > 0) {
        discard(toDiscard);
        currentEntry.remaining -= toDiscard;
      }
      if (currentEntry.remaining > 0) return false;
      return unpacker.skipPadding();
    },
    validateEOF() {
      if (strict) {
        if (!eof) throw truncateErr;
        if (available() > 0) {
          if (pull(available()).some((byte) => byte !== 0)) throw new Error("Invalid EOF.");
        }
      }
    }
  };
  return unpacker;
}
function isZeroBlock(block) {
  if (block.byteOffset % 8 === 0) {
    const view = new BigUint64Array(block.buffer, block.byteOffset, block.length / 8);
    for (let i = 0; i < view.length; i++) if (view[i] !== 0n) return false;
    return true;
  }
  for (let i = 0; i < block.length; i++) if (block[i] !== 0) return false;
  return true;
}

// node_modules/.pnpm/modern-tar@0.7.3/node_modules/modern-tar/dist/web/index.js
function createGzipEncoder() {
  return new CompressionStream("gzip");
}
function createGzipDecoder() {
  return new DecompressionStream("gzip");
}
function createTarPacker2() {
  let streamController;
  let packer;
  return {
    readable: new ReadableStream({ start(controller) {
      streamController = controller;
      packer = createTarPacker(controller.enqueue.bind(controller), controller.error.bind(controller), controller.close.bind(controller));
    } }),
    controller: {
      add(header) {
        const bodyless = isBodyless(header);
        const h = { ...header };
        if (bodyless) h.size = 0;
        packer.add(h);
        if (bodyless) packer.endEntry();
        return new WritableStream({
          write(chunk) {
            packer.write(chunk);
          },
          close() {
            if (!bodyless) packer.endEntry();
          },
          abort(reason) {
            streamController.error(reason);
          }
        });
      },
      finalize() {
        packer.finalize();
      },
      error(err) {
        streamController.error(err);
      }
    }
  };
}
async function streamToBuffer(stream) {
  const chunks = [];
  const reader = stream.getReader();
  let totalLength = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      totalLength += value.length;
    }
    const result = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }
    return result;
  } finally {
    reader.releaseLock();
  }
}
var drain = (stream) => stream.pipeTo(new WritableStream());
function createTarDecoder(options = {}) {
  const unpacker = createUnpacker(options);
  let bodyController = null;
  let pumping = false;
  const pump = (controller) => {
    if (pumping) return;
    pumping = true;
    try {
      while (true) if (unpacker.isEntryActive()) {
        if (bodyController) {
          if (unpacker.streamBody((c) => (bodyController.enqueue(c), true)) === 0 && !unpacker.isBodyComplete()) break;
        } else if (!unpacker.skipEntry()) break;
        if (unpacker.isBodyComplete()) {
          try {
            bodyController?.close();
          } catch {
          }
          bodyController = null;
          if (!unpacker.skipPadding()) break;
        }
      } else {
        const header = unpacker.readHeader();
        if (header === null || header === void 0) break;
        controller.enqueue({
          header,
          body: new ReadableStream({
            start(c) {
              if (header.size === 0) c.close();
              else bodyController = c;
            },
            pull: () => pump(controller),
            cancel() {
              bodyController = null;
              pump(controller);
            }
          })
        });
      }
    } catch (error) {
      try {
        bodyController?.error(error);
      } catch {
      }
      bodyController = null;
      throw error;
    } finally {
      pumping = false;
    }
  };
  return new TransformStream({
    transform(chunk, controller) {
      try {
        unpacker.write(chunk);
        pump(controller);
      } catch (error) {
        try {
          bodyController?.error(error);
        } catch {
        }
        throw error;
      }
    },
    flush(controller) {
      try {
        unpacker.end();
        pump(controller);
        unpacker.validateEOF();
        if (unpacker.isEntryActive() && !unpacker.isBodyComplete()) try {
          bodyController?.close();
        } catch {
        }
      } catch (error) {
        try {
          bodyController?.error(error);
        } catch {
        }
        throw error;
      }
    }
  }, void 0, { highWaterMark: 1 });
}
async function packTar(entries) {
  const { readable, controller } = createTarPacker2();
  await (async () => {
    for (const entry of entries) {
      const entryStream = controller.add(entry.header);
      const body = "body" in entry ? entry.body : entry.data;
      if (!body) {
        await entryStream.close();
        continue;
      }
      if (body instanceof ReadableStream) await body.pipeTo(entryStream);
      else if (body instanceof Blob) await body.stream().pipeTo(entryStream);
      else try {
        const chunk = await normalizeBody(body);
        if (chunk.length > 0) {
          const writer = entryStream.getWriter();
          await writer.write(chunk);
          await writer.close();
        } else await entryStream.close();
      } catch {
        throw new TypeError(`Unsupported content type for entry "${entry.header.name}".`);
      }
    }
  })().then(() => controller.finalize()).catch((err) => controller.error(err));
  return new Uint8Array(await streamToBuffer(readable));
}
async function unpackTar(archive, options = {}) {
  const sourceStream = archive instanceof ReadableStream ? archive : new ReadableStream({ start(controller) {
    controller.enqueue(archive instanceof Uint8Array ? archive : new Uint8Array(archive));
    controller.close();
  } });
  const results = [];
  const entryStream = sourceStream.pipeThrough(createTarDecoder(options));
  for await (const entry of entryStream) {
    let processedHeader;
    try {
      processedHeader = transformHeader(entry.header, options);
    } catch (error) {
      await entry.body.cancel();
      throw error;
    }
    if (processedHeader === null) {
      await drain(entry.body);
      continue;
    }
    if (isBodyless(processedHeader)) {
      await drain(entry.body);
      results.push({ header: processedHeader });
    } else results.push({
      header: processedHeader,
      data: await streamToBuffer(entry.body)
    });
  }
  return results;
}

// dist/commands/tar/archive.js
var import_seek_bzip = __toESM(require_lib(), 1);

// dist/commands/tar/bzip2-compress.js
var CRC32_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i << 24;
    for (let j = 0; j < 8; j++) {
      c = c & 2147483648 ? c << 1 ^ 79764919 : c << 1;
    }
    table[i] = c >>> 0;
  }
  return table;
})();
function crc32Update(crc, byte) {
  return (crc << 8 ^ CRC32_TABLE[(crc >>> 24 ^ byte) & 255]) >>> 0;
}
var BitWriter = class {
  buffer = [];
  current = 0;
  bitCount = 0;
  writeBits(n, value) {
    for (let i = n - 1; i >= 0; i--) {
      this.current = this.current << 1 | value >>> i & 1;
      this.bitCount++;
      if (this.bitCount === 8) {
        this.buffer.push(this.current);
        this.current = 0;
        this.bitCount = 0;
      }
    }
  }
  writeBit(value) {
    this.current = this.current << 1 | value & 1;
    this.bitCount++;
    if (this.bitCount === 8) {
      this.buffer.push(this.current);
      this.current = 0;
      this.bitCount = 0;
    }
  }
  finish() {
    if (this.bitCount > 0) {
      this.buffer.push(this.current << 8 - this.bitCount);
    }
    return new Uint8Array(this.buffer);
  }
};
function rle1Encode(data) {
  const out = [];
  let i = 0;
  while (i < data.length) {
    const ch = data[i];
    let runLen = 1;
    while (i + runLen < data.length && data[i + runLen] === ch && runLen < 255) {
      runLen++;
    }
    if (runLen >= 4) {
      out.push(ch, ch, ch, ch);
      out.push(runLen - 4);
      i += runLen;
    } else {
      out.push(ch);
      i++;
    }
  }
  return new Uint8Array(out);
}
function bwt(data) {
  const n = data.length;
  if (n === 0) {
    return { transformed: new Uint8Array(0), pointer: 0 };
  }
  const sa = buildSuffixArrayForRotations(data);
  const transformed = new Uint8Array(n);
  let pointer = 0;
  for (let i = 0; i < n; i++) {
    if (sa[i] === 0) {
      pointer = i;
      transformed[i] = data[n - 1];
    } else {
      transformed[i] = data[sa[i] - 1];
    }
  }
  return { transformed, pointer };
}
function buildSuffixArrayForRotations(data) {
  const n = data.length;
  const sa = new Int32Array(n);
  const rank = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    sa[i] = i;
    rank[i] = data[i];
  }
  for (let gap = 1; gap < n; gap *= 2) {
    const r = rank.slice();
    sa.sort((a, b) => {
      if (r[a] !== r[b])
        return r[a] - r[b];
      return r[(a + gap) % n] - r[(b + gap) % n];
    });
    rank[sa[0]] = 0;
    for (let i = 1; i < n; i++) {
      if (r[sa[i]] === r[sa[i - 1]] && r[(sa[i] + gap) % n] === r[(sa[i - 1] + gap) % n]) {
        rank[sa[i]] = rank[sa[i - 1]];
      } else {
        rank[sa[i]] = rank[sa[i - 1]] + 1;
      }
    }
    if (rank[sa[n - 1]] === n - 1)
      break;
  }
  return sa;
}
function mtfEncode(data, symbolsInUse) {
  const mtfList = [];
  for (let i = 0; i < 256; i++) {
    if (symbolsInUse[i]) {
      mtfList.push(i);
    }
  }
  const byteToIndex = new Array(256).fill(-1);
  for (let i = 0; i < mtfList.length; i++) {
    byteToIndex[mtfList[i]] = i;
  }
  const encoded = new Uint16Array(data.length);
  const list = mtfList.slice();
  for (let i = 0; i < data.length; i++) {
    const byte = data[i];
    let pos = 0;
    while (list[pos] !== byte)
      pos++;
    encoded[i] = pos;
    if (pos > 0) {
      const val = list[pos];
      for (let j = pos; j > 0; j--) {
        list[j] = list[j - 1];
      }
      list[0] = val;
    }
  }
  return { encoded, length: data.length };
}
function rle2Encode(mtfData, mtfLen, numSymbolsInUse) {
  const RUNA = 0;
  const RUNB = 1;
  const eob = numSymbolsInUse + 1;
  const symbols = [];
  let i = 0;
  while (i < mtfLen) {
    if (mtfData[i] === 0) {
      let runLen = 0;
      while (i < mtfLen && mtfData[i] === 0) {
        runLen++;
        i++;
      }
      let n = runLen;
      while (n > 0) {
        n--;
        if (n & 1) {
          symbols.push(RUNB);
        } else {
          symbols.push(RUNA);
        }
        n >>>= 1;
      }
    } else {
      symbols.push(mtfData[i] + 1);
      i++;
    }
  }
  symbols.push(eob);
  const result = new Uint16Array(symbols.length);
  for (let j = 0; j < symbols.length; j++) {
    result[j] = symbols[j];
  }
  return { symbols: result, length: symbols.length, eob };
}
function buildHuffmanTable(freqs, numSymbols, maxCodeLen) {
  if (numSymbols <= 1) {
    const lengths = new Array(freqs.length).fill(0);
    for (let i = 0; i < freqs.length; i++) {
      if (freqs[i] > 0)
        lengths[i] = 1;
    }
    return { codeLengths: lengths, maxLen: 1, minLen: 1 };
  }
  const nodes = [];
  for (let i = 0; i < freqs.length; i++) {
    if (freqs[i] > 0) {
      nodes.push({ freq: freqs[i], symbol: i, left: null, right: null });
    }
  }
  if (nodes.length === 0) {
    return {
      codeLengths: new Array(freqs.length).fill(0),
      maxLen: 0,
      minLen: 0
    };
  }
  if (nodes.length === 1) {
    const lengths = new Array(freqs.length).fill(0);
    lengths[nodes[0].symbol] = 1;
    return { codeLengths: lengths, maxLen: 1, minLen: 1 };
  }
  while (nodes.length > 1) {
    nodes.sort((a, b) => a.freq - b.freq);
    const left = nodes.shift();
    const right = nodes.shift();
    nodes.push({
      freq: left.freq + right.freq,
      symbol: -1,
      left,
      right
    });
  }
  const codeLengths = new Array(freqs.length).fill(0);
  function traverse(node, depth) {
    if (!node.left && !node.right) {
      codeLengths[node.symbol] = depth;
      return;
    }
    if (node.left)
      traverse(node.left, depth + 1);
    if (node.right)
      traverse(node.right, depth + 1);
  }
  traverse(nodes[0], 0);
  let changed = true;
  while (changed) {
    changed = false;
    for (let i = 0; i < codeLengths.length; i++) {
      if (codeLengths[i] > maxCodeLen) {
        codeLengths[i] = maxCodeLen;
        changed = true;
      }
    }
    if (changed) {
      let kraft = 0;
      for (let i = 0; i < codeLengths.length; i++) {
        if (codeLengths[i] > 0) {
          kraft += 1 / (1 << codeLengths[i]);
        }
      }
      if (kraft > 1) {
        for (let len = 1; len < maxCodeLen && kraft > 1; len++) {
          for (let i = 0; i < codeLengths.length && kraft > 1; i++) {
            if (codeLengths[i] === len) {
              codeLengths[i]++;
              kraft -= 1 / (1 << len) - 1 / (1 << len + 1);
            }
          }
        }
      }
      changed = false;
      for (let i = 0; i < codeLengths.length; i++) {
        if (codeLengths[i] > maxCodeLen) {
          changed = true;
          break;
        }
      }
    }
  }
  let minLen = maxCodeLen;
  let actualMaxLen = 0;
  for (let i = 0; i < codeLengths.length; i++) {
    if (codeLengths[i] > 0) {
      if (codeLengths[i] < minLen)
        minLen = codeLengths[i];
      if (codeLengths[i] > actualMaxLen)
        actualMaxLen = codeLengths[i];
    }
  }
  return { codeLengths, maxLen: actualMaxLen, minLen };
}
function generateCanonicalCodes(codeLengths, numSymbols) {
  const codes = new Array(numSymbols).fill(0);
  const lengths = codeLengths.slice(0, numSymbols);
  const maxLen = Math.max(...lengths, 0);
  const blCount = new Array(maxLen + 1).fill(0);
  for (let i = 0; i < numSymbols; i++) {
    if (lengths[i] > 0)
      blCount[lengths[i]]++;
  }
  const nextCode = new Array(maxLen + 1).fill(0);
  let code = 0;
  for (let bits = 1; bits <= maxLen; bits++) {
    code = code + blCount[bits - 1] << 1;
    nextCode[bits] = code;
  }
  for (let i = 0; i < numSymbols; i++) {
    if (lengths[i] > 0) {
      codes[i] = nextCode[lengths[i]]++;
    }
  }
  return { codes, lengths };
}
function compressBlock(writer, blockData, blockCRC) {
  writer.writeBits(24, 3227993);
  writer.writeBits(24, 2511705);
  writer.writeBits(32, blockCRC);
  writer.writeBit(0);
  const rle1Data = rle1Encode(blockData);
  const { transformed, pointer } = bwt(rle1Data);
  writer.writeBits(24, pointer);
  const symbolsInUse = new Array(256).fill(false);
  for (let i = 0; i < transformed.length; i++) {
    symbolsInUse[transformed[i]] = true;
  }
  const inUse16 = new Array(16).fill(false);
  for (let i = 0; i < 16; i++) {
    for (let j = 0; j < 16; j++) {
      if (symbolsInUse[i * 16 + j]) {
        inUse16[i] = true;
        break;
      }
    }
  }
  for (let i = 0; i < 16; i++) {
    writer.writeBit(inUse16[i] ? 1 : 0);
  }
  for (let i = 0; i < 16; i++) {
    if (inUse16[i]) {
      for (let j = 0; j < 16; j++) {
        writer.writeBit(symbolsInUse[i * 16 + j] ? 1 : 0);
      }
    }
  }
  let numSymbolsInUse = 0;
  for (let i = 0; i < 256; i++) {
    if (symbolsInUse[i])
      numSymbolsInUse++;
  }
  const { encoded: mtfData, length: mtfLen } = mtfEncode(transformed, symbolsInUse);
  const { symbols, length: symLen } = rle2Encode(mtfData, mtfLen, numSymbolsInUse);
  const alphaSize = numSymbolsInUse + 2;
  const GROUP_SIZE = 50;
  const nSelectors = Math.ceil(symLen / GROUP_SIZE);
  let nGroups;
  if (symLen < 200)
    nGroups = 2;
  else if (symLen < 600)
    nGroups = 3;
  else if (symLen < 1200)
    nGroups = 4;
  else if (symLen < 2400)
    nGroups = 5;
  else
    nGroups = 6;
  if (nGroups > nSelectors)
    nGroups = Math.max(2, nSelectors);
  const groupFreqs = [];
  for (let t = 0; t < nGroups; t++) {
    groupFreqs.push(new Array(alphaSize).fill(0));
  }
  const selectors = new Int32Array(nSelectors);
  for (let s = 0; s < nSelectors; s++) {
    selectors[s] = s % nGroups;
  }
  for (let s = 0; s < nSelectors; s++) {
    const start = s * GROUP_SIZE;
    const end = Math.min(start + GROUP_SIZE, symLen);
    const g = selectors[s];
    for (let i = start; i < end; i++) {
      groupFreqs[g][symbols[i]]++;
    }
  }
  function ensureMinFreq(freqs) {
    for (let i = 0; i < alphaSize; i++) {
      if (freqs[i] < 1)
        freqs[i] = 1;
    }
  }
  const tables = [];
  for (let t = 0; t < nGroups; t++) {
    ensureMinFreq(groupFreqs[t]);
    tables.push(buildHuffmanTable(groupFreqs[t], alphaSize, 20));
  }
  for (let iter = 0; iter < 4; iter++) {
    for (let t = 0; t < nGroups; t++) {
      groupFreqs[t].fill(0);
    }
    for (let s = 0; s < nSelectors; s++) {
      const start = s * GROUP_SIZE;
      const end = Math.min(start + GROUP_SIZE, symLen);
      let bestGroup = 0;
      let bestCost = Infinity;
      for (let t = 0; t < nGroups; t++) {
        let cost = 0;
        for (let i = start; i < end; i++) {
          cost += tables[t].codeLengths[symbols[i]] || 20;
        }
        if (cost < bestCost) {
          bestCost = cost;
          bestGroup = t;
        }
      }
      selectors[s] = bestGroup;
      for (let i = start; i < end; i++) {
        groupFreqs[bestGroup][symbols[i]]++;
      }
    }
    for (let t = 0; t < nGroups; t++) {
      ensureMinFreq(groupFreqs[t]);
      tables[t] = buildHuffmanTable(groupFreqs[t], alphaSize, 20);
    }
  }
  writer.writeBits(3, nGroups);
  writer.writeBits(15, nSelectors);
  const selectorMtf = [];
  const selectorList = [];
  for (let i = 0; i < nGroups; i++)
    selectorList.push(i);
  for (let s = 0; s < nSelectors; s++) {
    const val = selectors[s];
    let pos = 0;
    while (selectorList[pos] !== val)
      pos++;
    selectorMtf.push(pos);
    if (pos > 0) {
      const v = selectorList[pos];
      for (let j = pos; j > 0; j--) {
        selectorList[j] = selectorList[j - 1];
      }
      selectorList[0] = v;
    }
  }
  for (let s = 0; s < nSelectors; s++) {
    for (let j = 0; j < selectorMtf[s]; j++) {
      writer.writeBit(1);
    }
    writer.writeBit(0);
  }
  for (let t = 0; t < nGroups; t++) {
    const lengths = tables[t].codeLengths;
    let currentLen = lengths[0];
    writer.writeBits(5, currentLen);
    for (let i = 0; i < alphaSize; i++) {
      const targetLen = lengths[i];
      while (currentLen < targetLen) {
        writer.writeBit(1);
        writer.writeBit(0);
        currentLen++;
      }
      while (currentLen > targetLen) {
        writer.writeBit(1);
        writer.writeBit(1);
        currentLen--;
      }
      writer.writeBit(0);
    }
  }
  for (let t = 0; t < nGroups; t++) {
    const { codes, lengths } = generateCanonicalCodes(tables[t].codeLengths, alphaSize);
    tables[t] = Object.assign(tables[t], { _codes: codes, _lengths: lengths });
  }
  let selectorIdx = 0;
  let groupPos = 0;
  for (let i = 0; i < symLen; i++) {
    if (groupPos === 0 || groupPos >= GROUP_SIZE) {
      if (i > 0)
        selectorIdx++;
      groupPos = 0;
    }
    const tableIdx = selectors[selectorIdx];
    const table = tables[tableIdx];
    const sym = symbols[i];
    const len = table._lengths[sym];
    const code = table._codes[sym];
    if (len > 0) {
      writer.writeBits(len, code);
    }
    groupPos++;
  }
}
var DEFAULT_MAX_COMPRESS_SIZE = 10 * 1024 * 1024;
function bzip2Compress(data, blockSizeLevel = 9, maxSize = DEFAULT_MAX_COMPRESS_SIZE) {
  if (blockSizeLevel < 1 || blockSizeLevel > 9) {
    throw new Error("Block size level must be 1-9");
  }
  if (data.length > maxSize) {
    throw new Error(`Input too large for bzip2 compression (${data.length} bytes, max ${maxSize})`);
  }
  const blockSize = blockSizeLevel * 1e5;
  const writer = new BitWriter();
  writer.writeBits(8, 66);
  writer.writeBits(8, 90);
  writer.writeBits(8, 104);
  writer.writeBits(8, 48 + blockSizeLevel);
  let combinedCRC = 0;
  let offset = 0;
  while (offset < data.length) {
    const end = Math.min(offset + blockSize, data.length);
    const blockData = data.subarray(offset, end);
    let blockCRC = 4294967295;
    for (let i = 0; i < blockData.length; i++) {
      blockCRC = crc32Update(blockCRC, blockData[i]);
    }
    blockCRC = ~blockCRC >>> 0;
    combinedCRC = (combinedCRC << 1 | combinedCRC >>> 31) >>> 0;
    combinedCRC = (combinedCRC ^ blockCRC) >>> 0;
    compressBlock(writer, blockData, blockCRC);
    offset = end;
  }
  writer.writeBits(24, 1536581);
  writer.writeBits(24, 3690640);
  writer.writeBits(32, combinedCRC);
  return writer.finish();
}

// dist/commands/tar/archive.js
var lzma = null;
var lzmaLoadError = null;
async function getLzma() {
  if (lzma)
    return lzma;
  if (lzmaLoadError)
    throw lzmaLoadError;
  try {
    lzma = await DefenseInDepthBox.runTrustedAsync(() => import("node-liblzma"));
    return lzma;
  } catch {
    lzmaLoadError = new Error("xz compression requires node-liblzma which failed to load. Install liblzma-dev (apt) or xz (brew) and reinstall dependencies.");
    throw lzmaLoadError;
  }
}
var zstd = null;
var zstdLoadError = null;
async function getZstd() {
  if (zstd)
    return zstd;
  if (zstdLoadError)
    throw zstdLoadError;
  try {
    zstd = await DefenseInDepthBox.runTrustedAsync(() => import("@mongodb-js/zstd"));
    return zstd;
  } catch {
    zstdLoadError = new Error("zstd compression requires @mongodb-js/zstd which is not installed. Install it with: npm install @mongodb-js/zstd");
    throw zstdLoadError;
  }
}
var MAX_ARCHIVE_SIZE = 100 * 1024 * 1024;
var TAR_BLOCK_SIZE = 512;
var MAX_ENTRIES = 1e4;
function toModernTarEntry(entry) {
  let type = "file";
  if (entry.isDirectory) {
    type = "directory";
  } else if (entry.isSymlink) {
    type = "symlink";
  }
  let name = entry.name;
  if (entry.isDirectory && !name.endsWith("/")) {
    name += "/";
  }
  let body;
  if (entry.content !== void 0) {
    if (typeof entry.content === "string") {
      body = new TextEncoder().encode(entry.content);
    } else {
      body = entry.content;
    }
  }
  const size = entry.isDirectory || entry.isSymlink ? 0 : body?.length ?? 0;
  return {
    header: {
      name,
      mode: entry.mode ?? (entry.isDirectory ? 493 : 420),
      uid: entry.uid ?? 0,
      gid: entry.gid ?? 0,
      size,
      mtime: entry.mtime ?? /* @__PURE__ */ new Date(),
      type,
      linkname: entry.linkTarget ?? "",
      uname: "user",
      gname: "user"
    },
    body
  };
}
async function createArchive(entries) {
  const modernEntries = entries.map(toModernTarEntry);
  return packTar(modernEntries);
}
async function createCompressedArchive(entries) {
  const tarBuffer = await createArchive(entries);
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(tarBuffer);
      controller.close();
    }
  });
  const compressedStream = stream.pipeThrough(createGzipEncoder());
  const reader = compressedStream.getReader();
  const chunks = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done)
      break;
    chunks.push(value);
  }
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const result = new Uint8Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.length;
  }
  return result;
}
async function parseArchive(data) {
  if (data.length > MAX_ARCHIVE_SIZE) {
    return {
      entries: [],
      error: `Archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
    };
  }
  if (data.length < TAR_BLOCK_SIZE || data.length % TAR_BLOCK_SIZE !== 0) {
    return {
      entries: [],
      error: "Invalid tar archive format"
    };
  }
  try {
    const modernEntries = await unpackTar(data);
    const entries = [];
    for (const entry of modernEntries) {
      if (entries.length >= MAX_ENTRIES) {
        return { entries, error: `Too many entries (max ${MAX_ENTRIES})` };
      }
      let type = "file";
      switch (entry.header.type) {
        case "directory":
          type = "directory";
          break;
        case "symlink":
          type = "symlink";
          break;
        case "link":
          type = "hardlink";
          break;
        case "file":
          type = "file";
          break;
        default:
          type = "other";
      }
      entries.push({
        name: entry.header.name,
        mode: entry.header.mode ?? 420,
        uid: entry.header.uid ?? 0,
        gid: entry.header.gid ?? 0,
        size: entry.header.size,
        mtime: entry.header.mtime ?? /* @__PURE__ */ new Date(),
        type,
        linkTarget: entry.header.linkname || void 0,
        content: entry.data ?? new Uint8Array(0)
      });
    }
    return { entries };
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return { entries: [], error: msg };
  }
}
async function parseCompressedArchive(data) {
  if (data.length > MAX_ARCHIVE_SIZE) {
    return {
      entries: [],
      error: `Archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
    };
  }
  try {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(data);
        controller.close();
      }
    });
    const decompressedStream = stream.pipeThrough(createGzipDecoder());
    const reader = decompressedStream.getReader();
    const chunks = [];
    let totalLength = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done)
        break;
      totalLength += value.length;
      if (totalLength > MAX_ARCHIVE_SIZE) {
        await reader.cancel();
        return {
          entries: [],
          error: `Decompressed archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
        };
      }
      chunks.push(value);
    }
    const tarBuffer = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      tarBuffer.set(chunk, offset);
      offset += chunk.length;
    }
    return parseArchive(tarBuffer);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return { entries: [], error: `Decompression failed: ${msg}` };
  }
}
function isGzipCompressed(data) {
  return data.length >= 2 && data[0] === 31 && data[1] === 139;
}
function isBzip2Compressed(data) {
  return data.length >= 3 && data[0] === 66 && data[1] === 90 && data[2] === 104;
}
function isXzCompressed(data) {
  return data.length >= 6 && data[0] === 253 && data[1] === 55 && data[2] === 122 && data[3] === 88 && data[4] === 90 && data[5] === 0;
}
async function decompressBzip2(data) {
  const decompressed = import_seek_bzip.default.decode(Buffer.from(data));
  return new Uint8Array(decompressed);
}
async function compressBzip2(data) {
  return bzip2Compress(data, 9);
}
async function decompressXz(data) {
  const lzmaModule = await getLzma();
  const decompressed = lzmaModule.unxzSync(Buffer.from(data));
  return new Uint8Array(decompressed);
}
async function compressXz(data) {
  const lzmaModule = await getLzma();
  const compressed = lzmaModule.xzSync(Buffer.from(data));
  return new Uint8Array(compressed);
}
async function createBzip2CompressedArchive(entries) {
  const tarBuffer = await createArchive(entries);
  return compressBzip2(tarBuffer);
}
async function createXzCompressedArchive(entries, options) {
  if (!options?.allowNativeCodecs) {
    throw new Error("xz compression is disabled by default (native codec risk). Pass { allowNativeCodecs: true } to opt in.");
  }
  const tarBuffer = await createArchive(entries);
  return compressXz(tarBuffer);
}
async function parseBzip2CompressedArchive(data) {
  if (data.length > MAX_ARCHIVE_SIZE) {
    return {
      entries: [],
      error: `Archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
    };
  }
  try {
    const tarBuffer = await decompressBzip2(data);
    if (tarBuffer.length > MAX_ARCHIVE_SIZE) {
      return {
        entries: [],
        error: `Decompressed archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
      };
    }
    return parseArchive(tarBuffer);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return { entries: [], error: msg };
  }
}
async function parseXzCompressedArchive(data, options) {
  if (!options?.allowNativeCodecs) {
    return {
      entries: [],
      error: "xz decompression is disabled by default (native codec risk). Pass { allowNativeCodecs: true } to opt in, or decompress the archive externally before extraction."
    };
  }
  if (data.length > MAX_ARCHIVE_SIZE) {
    return {
      entries: [],
      error: `Archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
    };
  }
  try {
    const tarBuffer = await decompressXz(data);
    if (tarBuffer.length > MAX_ARCHIVE_SIZE) {
      return {
        entries: [],
        error: `Decompressed archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
      };
    }
    return parseArchive(tarBuffer);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return { entries: [], error: msg };
  }
}
function isZstdCompressed(data) {
  return data.length >= 4 && data[0] === 40 && data[1] === 181 && data[2] === 47 && data[3] === 253;
}
async function compressZstd(data) {
  const zstdModule = await getZstd();
  const compressed = await zstdModule.compress(Buffer.from(data), 3);
  return new Uint8Array(compressed);
}
async function decompressZstd(data) {
  const zstdModule = await getZstd();
  const decompressed = await zstdModule.decompress(Buffer.from(data));
  return new Uint8Array(decompressed);
}
async function createZstdCompressedArchive(entries, options) {
  if (!options?.allowNativeCodecs) {
    throw new Error("zstd compression is disabled by default (native codec risk). Pass { allowNativeCodecs: true } to opt in.");
  }
  const tarBuffer = await createArchive(entries);
  return compressZstd(tarBuffer);
}
async function parseZstdCompressedArchive(data, options) {
  if (!options?.allowNativeCodecs) {
    return {
      entries: [],
      error: "zstd decompression is disabled by default (native codec risk). Pass { allowNativeCodecs: true } to opt in, or decompress the archive externally before extraction."
    };
  }
  if (data.length > MAX_ARCHIVE_SIZE) {
    return {
      entries: [],
      error: `Archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
    };
  }
  try {
    const tarBuffer = await decompressZstd(data);
    if (tarBuffer.length > MAX_ARCHIVE_SIZE) {
      return {
        entries: [],
        error: `Decompressed archive too large (max ${MAX_ARCHIVE_SIZE} bytes)`
      };
    }
    return parseArchive(tarBuffer);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return { entries: [], error: msg };
  }
}

// dist/commands/tar/tar-options.js
function parseOptions(args) {
  const options = {
    create: false,
    append: false,
    update: false,
    extract: false,
    list: false,
    file: "",
    autoCompress: false,
    gzip: false,
    bzip2: false,
    xz: false,
    zstd: false,
    verbose: false,
    toStdout: false,
    keepOldFiles: false,
    touch: false,
    directory: "",
    preserve: false,
    absoluteNames: false,
    strip: 0,
    exclude: [],
    filesFrom: "",
    excludeFrom: "",
    wildcards: false
  };
  const files = [];
  let i = 0;
  while (i < args.length) {
    const arg = args[i];
    if (arg.startsWith("-") && !arg.startsWith("--") && arg.length > 2) {
      if (/^-\d+$/.test(arg)) {
        files.push(arg);
        i++;
        continue;
      }
      for (let j = 1; j < arg.length; j++) {
        const char = arg[j];
        switch (char) {
          case "c":
            options.create = true;
            break;
          case "r":
            options.append = true;
            break;
          case "u":
            options.update = true;
            break;
          case "x":
            options.extract = true;
            break;
          case "t":
            options.list = true;
            break;
          case "a":
            options.autoCompress = true;
            break;
          case "z":
            options.gzip = true;
            break;
          case "j":
            options.bzip2 = true;
            break;
          case "J":
            options.xz = true;
            break;
          case "v":
            options.verbose = true;
            break;
          case "O":
            options.toStdout = true;
            break;
          case "k":
            options.keepOldFiles = true;
            break;
          case "m":
            options.touch = true;
            break;
          case "p":
            options.preserve = true;
            break;
          case "P":
            options.absoluteNames = true;
            break;
          case "f":
            if (j < arg.length - 1) {
              options.file = arg.substring(j + 1);
              j = arg.length;
            } else {
              i++;
              if (i >= args.length) {
                return {
                  ok: false,
                  error: {
                    stdout: "",
                    stderr: "tar: option requires an argument -- 'f'\n",
                    exitCode: 2
                  }
                };
              }
              options.file = args[i];
            }
            break;
          case "C":
            if (j < arg.length - 1) {
              options.directory = arg.substring(j + 1);
              j = arg.length;
            } else {
              i++;
              if (i >= args.length) {
                return {
                  ok: false,
                  error: {
                    stdout: "",
                    stderr: "tar: option requires an argument -- 'C'\n",
                    exitCode: 2
                  }
                };
              }
              options.directory = args[i];
            }
            break;
          case "T":
            if (j < arg.length - 1) {
              options.filesFrom = arg.substring(j + 1);
              j = arg.length;
            } else {
              i++;
              if (i >= args.length) {
                return {
                  ok: false,
                  error: {
                    stdout: "",
                    stderr: "tar: option requires an argument -- 'T'\n",
                    exitCode: 2
                  }
                };
              }
              options.filesFrom = args[i];
            }
            break;
          case "X":
            if (j < arg.length - 1) {
              options.excludeFrom = arg.substring(j + 1);
              j = arg.length;
            } else {
              i++;
              if (i >= args.length) {
                return {
                  ok: false,
                  error: {
                    stdout: "",
                    stderr: "tar: option requires an argument -- 'X'\n",
                    exitCode: 2
                  }
                };
              }
              options.excludeFrom = args[i];
            }
            break;
          default:
            return { ok: false, error: unknownOption("tar", `-${char}`) };
        }
      }
      i++;
      continue;
    }
    if (arg === "-c" || arg === "--create") {
      options.create = true;
    } else if (arg === "-r" || arg === "--append") {
      options.append = true;
    } else if (arg === "-u" || arg === "--update") {
      options.update = true;
    } else if (arg === "-x" || arg === "--extract" || arg === "--get") {
      options.extract = true;
    } else if (arg === "-t" || arg === "--list") {
      options.list = true;
    } else if (arg === "-a" || arg === "--auto-compress") {
      options.autoCompress = true;
    } else if (arg === "-z" || arg === "--gzip" || arg === "--gunzip") {
      options.gzip = true;
    } else if (arg === "-j" || arg === "--bzip2") {
      options.bzip2 = true;
    } else if (arg === "-J" || arg === "--xz") {
      options.xz = true;
    } else if (arg === "--zstd") {
      options.zstd = true;
    } else if (arg === "-v" || arg === "--verbose") {
      options.verbose = true;
    } else if (arg === "-O" || arg === "--to-stdout") {
      options.toStdout = true;
    } else if (arg === "-k" || arg === "--keep-old-files") {
      options.keepOldFiles = true;
    } else if (arg === "-m" || arg === "--touch") {
      options.touch = true;
    } else if (arg === "--wildcards") {
      options.wildcards = true;
    } else if (arg === "-p" || arg === "--preserve" || arg === "--preserve-permissions") {
      options.preserve = true;
    } else if (arg === "-P" || arg === "--absolute-names") {
      options.absoluteNames = true;
    } else if (arg === "-f" || arg === "--file") {
      i++;
      if (i >= args.length) {
        return {
          ok: false,
          error: {
            stdout: "",
            stderr: "tar: option requires an argument -- 'f'\n",
            exitCode: 2
          }
        };
      }
      options.file = args[i];
    } else if (arg.startsWith("--file=")) {
      options.file = arg.substring(7);
    } else if (arg === "-C" || arg === "--directory") {
      i++;
      if (i >= args.length) {
        return {
          ok: false,
          error: {
            stdout: "",
            stderr: "tar: option requires an argument -- 'C'\n",
            exitCode: 2
          }
        };
      }
      options.directory = args[i];
    } else if (arg.startsWith("--directory=")) {
      options.directory = arg.substring(12);
    } else if (arg.startsWith("--strip-components=") || arg.startsWith("--strip=")) {
      const val = arg.includes("--strip-components=") ? arg.substring(19) : arg.substring(8);
      const num = parseInt(val, 10);
      if (Number.isNaN(num) || num < 0) {
        return {
          ok: false,
          error: {
            stdout: "",
            stderr: `tar: invalid number for --strip: '${val}'
`,
            exitCode: 2
          }
        };
      }
      options.strip = num;
    } else if (arg.startsWith("--exclude=")) {
      options.exclude.push(arg.substring(10));
    } else if (arg === "--exclude") {
      i++;
      if (i >= args.length) {
        return {
          ok: false,
          error: {
            stdout: "",
            stderr: "tar: option '--exclude' requires an argument\n",
            exitCode: 2
          }
        };
      }
      options.exclude.push(args[i]);
    } else if (arg === "-T" || arg === "--files-from") {
      i++;
      if (i >= args.length) {
        return {
          ok: false,
          error: {
            stdout: "",
            stderr: "tar: option requires an argument -- 'T'\n",
            exitCode: 2
          }
        };
      }
      options.filesFrom = args[i];
    } else if (arg.startsWith("--files-from=")) {
      options.filesFrom = arg.substring(13);
    } else if (arg === "-X" || arg === "--exclude-from") {
      i++;
      if (i >= args.length) {
        return {
          ok: false,
          error: {
            stdout: "",
            stderr: "tar: option requires an argument -- 'X'\n",
            exitCode: 2
          }
        };
      }
      options.excludeFrom = args[i];
    } else if (arg.startsWith("--exclude-from=")) {
      options.excludeFrom = arg.substring(15);
    } else if (arg === "--") {
      files.push(...args.slice(i + 1));
      break;
    } else if (arg.startsWith("-")) {
      return { ok: false, error: unknownOption("tar", arg) };
    } else {
      files.push(arg);
    }
    i++;
  }
  return { ok: true, options, files };
}

// dist/commands/tar/tar.js
var BATCH_SIZE = 100;
var tarHelp = {
  name: "tar",
  summary: "manipulate tape archives",
  usage: "tar [options] [file...]",
  description: [
    "Create, extract, or list contents of tar archives.",
    "",
    "One of -c, -r, -u, -x, or -t is required to specify the operation."
  ],
  options: [
    "-c, --create           create a new archive",
    "-r, --append           append files to the end of an archive",
    "-u, --update           only append files newer than copy in archive",
    "-x, --extract          extract files from an archive",
    "-t, --list             list contents of an archive",
    "-f, --file=ARCHIVE     use archive file ARCHIVE",
    "-a, --auto-compress    use archive suffix to determine compression",
    "-z, --gzip             filter archive through gzip",
    "-j, --bzip2            filter archive through bzip2",
    "-J, --xz               filter archive through xz",
    "--zstd                 filter archive through zstd",
    "-v, --verbose          verbosely list files processed",
    "-O, --to-stdout        extract files to standard output",
    "-k, --keep-old-files   don't replace existing files when extracting",
    "-m, --touch            don't extract file modified time",
    "-C, --directory=DIR    change to directory DIR before performing operations",
    "-p, --preserve         preserve permissions",
    "-P, --absolute-names   do not strip leading '/' or block '..' paths",
    "-T, --files-from=FILE  read files to extract/create from FILE",
    "-X, --exclude-from=FILE read exclude patterns from FILE",
    "--strip=N              strip N leading path components on extraction",
    "--exclude=PATTERN      exclude files matching PATTERN",
    "--wildcards            use wildcards for pattern matching",
    "    --help             display this help and exit"
  ],
  examples: [
    "tar -cvf archive.tar file1 file2     Create archive from files",
    "tar -czvf archive.tar.gz dir/        Create gzip-compressed archive",
    "tar -cjvf archive.tar.bz2 dir/       Create bzip2-compressed archive",
    "tar -rf archive.tar newfile.txt      Append file to archive",
    "tar -uf archive.tar dir/             Update archive with newer files",
    "tar -xvf archive.tar                 Extract archive",
    "tar -xvf archive.tar -C /tmp         Extract to /tmp",
    "tar -tvf archive.tar                 List archive contents",
    "tar -xzf archive.tar.gz              Extract gzip archive",
    "tar -xf archive.tar file1.txt        Extract specific file",
    "tar -xOf archive.tar file.txt        Extract file to stdout",
    "tar -xf archive.tar --wildcards '*.txt'  Extract matching files"
  ]
};
function matchesExclude(path, patterns) {
  const basename = path.includes("/") ? path.substring(path.lastIndexOf("/") + 1) : path;
  for (const pattern of patterns) {
    const regex = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*\*/g, "<<<GLOBSTAR>>>").replace(/\*/g, "[^/]*").replace(/<<<GLOBSTAR>>>/g, ".*").replace(/\?/g, ".");
    if (createUserRegex(`^${regex}$`).test(path) || createUserRegex(`^${regex}/`).test(path)) {
      return true;
    }
    if (!pattern.includes("/") && createUserRegex(`^${regex}$`).test(basename)) {
      return true;
    }
  }
  return false;
}
function matchesWildcard(name, pattern) {
  const regex = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*\*/g, "<<<GLOBSTAR>>>").replace(/\*/g, "[^/]*").replace(/<<<GLOBSTAR>>>/g, ".*").replace(/\?/g, ".");
  const basename = name.includes("/") ? name.substring(name.lastIndexOf("/") + 1) : name;
  return createUserRegex(`^${regex}$`).test(name) || createUserRegex(`^${regex}$`).test(basename);
}
function stripComponents(path, count) {
  if (count <= 0)
    return path;
  const parts = path.split("/").filter((p) => p !== "");
  if (parts.length <= count)
    return "";
  return parts.slice(count).join("/");
}
function hasParentTraversal(path) {
  return path.split("/").some((part) => part === "..");
}
function sanitizeExtractionPath(path, absoluteNames) {
  if (absoluteNames) {
    return { safePath: path };
  }
  const withoutLeadingSlash = path.replace(/^\/+/, "");
  if (withoutLeadingSlash.length === 0) {
    return { safePath: "" };
  }
  if (hasParentTraversal(withoutLeadingSlash)) {
    return { error: "Path contains '..'" };
  }
  return { safePath: withoutLeadingSlash };
}
function formatDate(date) {
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec"
  ];
  const month = months[date.getMonth()];
  const day = date.getDate().toString().padStart(2, " ");
  const hours = date.getHours().toString().padStart(2, "0");
  const mins = date.getMinutes().toString().padStart(2, "0");
  return `${month} ${day} ${hours}:${mins}`;
}
async function collectFiles(ctx, basePath, relativePath, exclude) {
  const entries = [];
  const errors = [];
  const fullPath = ctx.fs.resolvePath(basePath, relativePath);
  try {
    const stat = await ctx.fs.stat(fullPath);
    if (matchesExclude(relativePath, exclude)) {
      return { entries, errors };
    }
    if (stat.isDirectory) {
      entries.push({
        name: relativePath,
        isDirectory: true,
        mode: stat.mode,
        mtime: stat.mtime
      });
      const items = await ctx.fs.readdir(fullPath);
      for (let i = 0; i < items.length; i += BATCH_SIZE) {
        const batch = items.slice(i, i + BATCH_SIZE);
        const results = await Promise.all(batch.map((item) => collectFiles(ctx, basePath, relativePath ? `${relativePath}/${item}` : item, exclude)));
        for (const result of results) {
          entries.push(...result.entries);
          errors.push(...result.errors);
        }
      }
    } else if (stat.isFile) {
      const content = await ctx.fs.readFileBuffer(fullPath);
      entries.push({
        name: relativePath,
        content,
        mode: stat.mode,
        mtime: stat.mtime
      });
    } else if (stat.isSymbolicLink) {
      const target = await ctx.fs.readlink(fullPath);
      entries.push({
        name: relativePath,
        isSymlink: true,
        linkTarget: target,
        mode: stat.mode,
        mtime: stat.mtime
      });
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : "unknown error";
    errors.push(`tar: ${relativePath}: ${msg}`);
  }
  return { entries, errors };
}
async function createTarArchive(ctx, options, files) {
  if (files.length === 0) {
    return {
      stdout: "",
      stderr: "tar: Cowardly refusing to create an empty archive\n",
      exitCode: 2
    };
  }
  const workDir = options.directory ? ctx.fs.resolvePath(ctx.cwd, options.directory) : ctx.cwd;
  const allEntries = [];
  const allErrors = [];
  let verboseOutput = "";
  for (const file of files) {
    const { entries, errors } = await collectFiles(ctx, workDir, file, options.exclude);
    allEntries.push(...entries);
    allErrors.push(...errors);
    if (options.verbose) {
      for (const entry of entries) {
        verboseOutput += `${entry.name}${entry.isDirectory ? "/" : ""}
`;
      }
    }
  }
  if (allEntries.length === 0 && allErrors.length > 0) {
    return {
      stdout: "",
      stderr: `${allErrors.join("\n")}
`,
      exitCode: 2
    };
  }
  let archiveData;
  try {
    if (options.gzip) {
      archiveData = await createCompressedArchive(allEntries);
    } else if (options.bzip2) {
      archiveData = await createBzip2CompressedArchive(allEntries);
    } else if (options.xz) {
      archiveData = await createXzCompressedArchive(allEntries);
    } else if (options.zstd) {
      archiveData = await createZstdCompressedArchive(allEntries);
    } else {
      archiveData = await createArchive(allEntries);
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : "unknown error";
    return {
      stdout: "",
      stderr: `tar: error creating archive: ${msg}
`,
      exitCode: 2
    };
  }
  let stdout = "";
  if (options.file && options.file !== "-") {
    const archivePath = ctx.fs.resolvePath(ctx.cwd, options.file);
    try {
      await ctx.fs.writeFile(archivePath, archiveData);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      return {
        stdout: "",
        stderr: `tar: ${options.file}: ${msg}
`,
        exitCode: 2
      };
    }
  } else {
    stdout = Buffer.from(archiveData).toString("latin1");
  }
  let stderr = verboseOutput;
  if (allErrors.length > 0) {
    stderr += `${allErrors.join("\n")}
`;
  }
  return { stdout, stderr, exitCode: allErrors.length > 0 ? 2 : 0 };
}
async function appendTarArchive(ctx, options, files) {
  if (!options.file || options.file === "-") {
    return {
      stdout: "",
      stderr: "tar: Cannot append to stdin/stdout\n",
      exitCode: 2
    };
  }
  if (files.length === 0) {
    return {
      stdout: "",
      stderr: "tar: Cowardly refusing to append nothing to archive\n",
      exitCode: 2
    };
  }
  const archivePath = ctx.fs.resolvePath(ctx.cwd, options.file);
  let existingData;
  try {
    existingData = await ctx.fs.readFileBuffer(archivePath);
  } catch {
    return {
      stdout: "",
      stderr: `tar: ${options.file}: Cannot open: No such file or directory
`,
      exitCode: 2
    };
  }
  const parseResult = await parseArchive(existingData);
  if (parseResult.error) {
    return {
      stdout: "",
      stderr: `tar: ${parseResult.error}
`,
      exitCode: 2
    };
  }
  const existingEntries = parseResult.entries.map((e) => ({
    name: e.name,
    content: e.content,
    mode: e.mode,
    mtime: e.mtime,
    isDirectory: e.type === "directory",
    isSymlink: e.type === "symlink",
    linkTarget: e.linkTarget,
    uid: e.uid,
    gid: e.gid
  }));
  const workDir = options.directory ? ctx.fs.resolvePath(ctx.cwd, options.directory) : ctx.cwd;
  const newEntries = [];
  const allErrors = [];
  let verboseOutput = "";
  for (const file of files) {
    const { entries, errors } = await collectFiles(ctx, workDir, file, options.exclude);
    newEntries.push(...entries);
    allErrors.push(...errors);
    if (options.verbose) {
      for (const entry of entries) {
        verboseOutput += `${entry.name}${entry.isDirectory ? "/" : ""}
`;
      }
    }
  }
  const allEntries = [...existingEntries, ...newEntries];
  let archiveData;
  try {
    archiveData = await createArchive(allEntries);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "unknown error";
    return {
      stdout: "",
      stderr: `tar: error creating archive: ${msg}
`,
      exitCode: 2
    };
  }
  try {
    await ctx.fs.writeFile(archivePath, archiveData);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "unknown error";
    return {
      stdout: "",
      stderr: `tar: ${options.file}: ${msg}
`,
      exitCode: 2
    };
  }
  let stderr = verboseOutput;
  if (allErrors.length > 0) {
    stderr += `${allErrors.join("\n")}
`;
  }
  return { stdout: "", stderr, exitCode: allErrors.length > 0 ? 2 : 0 };
}
async function updateTarArchive(ctx, options, files) {
  if (!options.file || options.file === "-") {
    return {
      stdout: "",
      stderr: "tar: Cannot update stdin/stdout\n",
      exitCode: 2
    };
  }
  if (files.length === 0) {
    return {
      stdout: "",
      stderr: "tar: Cowardly refusing to update with nothing\n",
      exitCode: 2
    };
  }
  const archivePath = ctx.fs.resolvePath(ctx.cwd, options.file);
  let existingData;
  try {
    existingData = await ctx.fs.readFileBuffer(archivePath);
  } catch {
    return {
      stdout: "",
      stderr: `tar: ${options.file}: Cannot open: No such file or directory
`,
      exitCode: 2
    };
  }
  const parseResult = await parseArchive(existingData);
  if (parseResult.error) {
    return {
      stdout: "",
      stderr: `tar: ${parseResult.error}
`,
      exitCode: 2
    };
  }
  const existingMtimes = /* @__PURE__ */ new Map();
  for (const entry of parseResult.entries) {
    existingMtimes.set(entry.name, entry.mtime);
  }
  const workDir = options.directory ? ctx.fs.resolvePath(ctx.cwd, options.directory) : ctx.cwd;
  const newEntries = [];
  const allErrors = [];
  let verboseOutput = "";
  for (const file of files) {
    const { entries, errors } = await collectFiles(ctx, workDir, file, options.exclude);
    allErrors.push(...errors);
    for (const entry of entries) {
      const existingMtime = existingMtimes.get(entry.name);
      if (!existingMtime || entry.mtime && entry.mtime.getTime() > existingMtime.getTime()) {
        newEntries.push(entry);
        if (options.verbose) {
          verboseOutput += `${entry.name}${entry.isDirectory ? "/" : ""}
`;
        }
      }
    }
  }
  if (newEntries.length === 0) {
    let stderr2 = "";
    if (allErrors.length > 0) {
      stderr2 = `${allErrors.join("\n")}
`;
    }
    return { stdout: "", stderr: stderr2, exitCode: allErrors.length > 0 ? 2 : 0 };
  }
  const updatedNames = new Set(newEntries.map((e) => e.name));
  const existingEntries = parseResult.entries.filter((e) => !updatedNames.has(e.name)).map((e) => ({
    name: e.name,
    content: e.content,
    mode: e.mode,
    mtime: e.mtime,
    isDirectory: e.type === "directory",
    isSymlink: e.type === "symlink",
    linkTarget: e.linkTarget,
    uid: e.uid,
    gid: e.gid
  }));
  const allEntries = [...existingEntries, ...newEntries];
  let archiveData;
  try {
    archiveData = await createArchive(allEntries);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "unknown error";
    return {
      stdout: "",
      stderr: `tar: error creating archive: ${msg}
`,
      exitCode: 2
    };
  }
  try {
    await ctx.fs.writeFile(archivePath, archiveData);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "unknown error";
    return {
      stdout: "",
      stderr: `tar: ${options.file}: ${msg}
`,
      exitCode: 2
    };
  }
  let stderr = verboseOutput;
  if (allErrors.length > 0) {
    stderr += `${allErrors.join("\n")}
`;
  }
  return { stdout: "", stderr, exitCode: allErrors.length > 0 ? 2 : 0 };
}
async function extractTarArchive(ctx, options, specificFiles) {
  let archiveData;
  if (options.file && options.file !== "-") {
    const archivePath = ctx.fs.resolvePath(ctx.cwd, options.file);
    try {
      archiveData = await ctx.fs.readFileBuffer(archivePath);
    } catch {
      return {
        stdout: "",
        stderr: `tar: ${options.file}: Cannot open: No such file or directory
`,
        exitCode: 2
      };
    }
  } else {
    archiveData = Uint8Array.from(ctx.stdin, (c) => c.charCodeAt(0));
  }
  let parseResult;
  const useGzip = options.gzip || isGzipCompressed(archiveData);
  const useBzip2 = options.bzip2 || isBzip2Compressed(archiveData);
  const useXz = options.xz || isXzCompressed(archiveData);
  const useZstd = options.zstd || isZstdCompressed(archiveData);
  if (useGzip) {
    parseResult = await parseCompressedArchive(archiveData);
  } else if (useBzip2) {
    parseResult = await parseBzip2CompressedArchive(archiveData);
  } else if (useXz) {
    parseResult = await parseXzCompressedArchive(archiveData);
  } else if (useZstd) {
    parseResult = await parseZstdCompressedArchive(archiveData);
  } else {
    parseResult = await parseArchive(archiveData);
  }
  if (parseResult.error) {
    return {
      stdout: "",
      stderr: `tar: ${parseResult.error}
`,
      exitCode: 2
    };
  }
  const workDir = options.directory ? ctx.fs.resolvePath(ctx.cwd, options.directory) : ctx.cwd;
  const normalizedSpecificFiles = options.absoluteNames ? specificFiles : specificFiles.map((f) => f.replace(/^\/+/, "")).filter((f) => f.length > 0);
  let verboseOutput = "";
  let stdoutContent = "";
  const errors = [];
  if (options.directory && !options.toStdout) {
    try {
      await ctx.fs.mkdir(workDir, { recursive: true });
    } catch {
    }
  }
  for (const entry of parseResult.entries) {
    const name = stripComponents(entry.name, options.strip);
    if (!name)
      continue;
    const sanitized = sanitizeExtractionPath(name, options.absoluteNames);
    if (sanitized.error) {
      errors.push(`tar: ${name}: ${sanitized.error}`);
      continue;
    }
    const safeName = sanitized.safePath ?? "";
    if (!safeName)
      continue;
    const displayName = safeName.endsWith("/") ? safeName.slice(0, -1) : safeName;
    if (normalizedSpecificFiles.length > 0) {
      let matches;
      if (options.wildcards) {
        matches = normalizedSpecificFiles.some((f) => matchesWildcard(safeName, f) || matchesWildcard(displayName, f) || safeName.startsWith(`${f}/`));
      } else {
        matches = normalizedSpecificFiles.some((f) => safeName === f || safeName.startsWith(`${f}/`) || displayName === f);
      }
      if (!matches)
        continue;
    }
    if (matchesExclude(safeName, options.exclude))
      continue;
    const targetPath = ctx.fs.resolvePath(workDir, safeName);
    try {
      if (entry.type === "directory") {
        if (options.toStdout)
          continue;
        await ctx.fs.mkdir(targetPath, { recursive: true });
        if (options.verbose) {
          verboseOutput += `${safeName}
`;
        }
      } else if (entry.type === "file") {
        if (options.toStdout) {
          stdoutContent += new TextDecoder().decode(entry.content);
          if (options.verbose) {
            verboseOutput += `${safeName}
`;
          }
          continue;
        }
        if (options.keepOldFiles) {
          try {
            await ctx.fs.stat(targetPath);
            if (options.verbose) {
              verboseOutput += `${safeName}: not overwritten, file exists
`;
            }
            continue;
          } catch {
          }
        }
        const parentDir = targetPath.substring(0, targetPath.lastIndexOf("/"));
        if (parentDir) {
          try {
            await ctx.fs.mkdir(parentDir, { recursive: true });
          } catch {
          }
        }
        await ctx.fs.writeFile(targetPath, entry.content);
        if (options.preserve && entry.mode) {
          try {
            await ctx.fs.chmod(targetPath, entry.mode);
          } catch {
          }
        }
        if (options.verbose) {
          verboseOutput += `${safeName}
`;
        }
      } else if (entry.type === "symlink" && entry.linkTarget) {
        if (options.toStdout)
          continue;
        if (!options.absoluteNames && (entry.linkTarget.startsWith("/") || hasParentTraversal(entry.linkTarget))) {
          errors.push(`tar: ${safeName}: unsafe symlink target`);
          continue;
        }
        if (options.keepOldFiles) {
          try {
            await ctx.fs.stat(targetPath);
            if (options.verbose) {
              verboseOutput += `${safeName}: not overwritten, file exists
`;
            }
            continue;
          } catch {
          }
        }
        const parentDir = targetPath.substring(0, targetPath.lastIndexOf("/"));
        if (parentDir) {
          try {
            await ctx.fs.mkdir(parentDir, { recursive: true });
          } catch {
          }
        }
        try {
          await ctx.fs.symlink(entry.linkTarget, targetPath);
        } catch {
        }
        if (options.verbose) {
          verboseOutput += `${safeName}
`;
        }
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      errors.push(`tar: ${safeName}: ${msg}`);
    }
  }
  let stderr = verboseOutput;
  if (errors.length > 0) {
    stderr += `${errors.join("\n")}
`;
  }
  return { stdout: stdoutContent, stderr, exitCode: errors.length > 0 ? 2 : 0 };
}
async function listTarArchive(ctx, options, specificFiles) {
  let archiveData;
  if (options.file && options.file !== "-") {
    const archivePath = ctx.fs.resolvePath(ctx.cwd, options.file);
    try {
      archiveData = await ctx.fs.readFileBuffer(archivePath);
    } catch {
      return {
        stdout: "",
        stderr: `tar: ${options.file}: Cannot open: No such file or directory
`,
        exitCode: 2
      };
    }
  } else {
    archiveData = Uint8Array.from(ctx.stdin, (c) => c.charCodeAt(0));
  }
  let parseResult;
  const useGzip = options.gzip || isGzipCompressed(archiveData);
  const useBzip2 = options.bzip2 || isBzip2Compressed(archiveData);
  const useXz = options.xz || isXzCompressed(archiveData);
  const useZstd = options.zstd || isZstdCompressed(archiveData);
  if (useGzip) {
    parseResult = await parseCompressedArchive(archiveData);
  } else if (useBzip2) {
    parseResult = await parseBzip2CompressedArchive(archiveData);
  } else if (useXz) {
    parseResult = await parseXzCompressedArchive(archiveData);
  } else if (useZstd) {
    parseResult = await parseZstdCompressedArchive(archiveData);
  } else {
    parseResult = await parseArchive(archiveData);
  }
  if (parseResult.error) {
    return {
      stdout: "",
      stderr: `tar: ${parseResult.error}
`,
      exitCode: 2
    };
  }
  let stdout = "";
  for (const entry of parseResult.entries) {
    const name = stripComponents(entry.name, options.strip);
    if (!name)
      continue;
    const displayName = name.endsWith("/") ? name.slice(0, -1) : name;
    if (specificFiles.length > 0) {
      let matches;
      if (options.wildcards) {
        matches = specificFiles.some((f) => matchesWildcard(name, f) || matchesWildcard(displayName, f) || name.startsWith(`${f}/`));
      } else {
        matches = specificFiles.some((f) => name === f || name.startsWith(`${f}/`) || displayName === f);
      }
      if (!matches)
        continue;
    }
    if (matchesExclude(name, options.exclude))
      continue;
    if (options.verbose) {
      const isDir = entry.type === "directory";
      const mode = formatMode(entry.mode, isDir);
      const owner = `${entry.uid}/${entry.gid}`;
      const size = entry.size.toString().padStart(8, " ");
      const date = formatDate(entry.mtime);
      let line = `${mode} ${owner.padEnd(10)} ${size} ${date} ${name}`;
      if (entry.type === "symlink" && entry.linkTarget) {
        line += ` -> ${entry.linkTarget}`;
      }
      stdout += `${line}
`;
    } else {
      stdout += `${name}
`;
    }
  }
  return { stdout, stderr: "", exitCode: 0 };
}
var tarCommand = {
  name: "tar",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(tarHelp);
    }
    const parsed = parseOptions(args);
    if (!parsed.ok) {
      return parsed.error;
    }
    const { options, files } = parsed;
    const opCount = [
      options.create,
      options.append,
      options.update,
      options.extract,
      options.list
    ].filter(Boolean).length;
    if (opCount === 0) {
      return {
        stdout: "",
        stderr: "tar: You must specify one of -c, -r, -u, -x, or -t\n",
        exitCode: 2
      };
    }
    if (opCount > 1) {
      return {
        stdout: "",
        stderr: "tar: You may not specify more than one of -c, -r, -u, -x, or -t\n",
        exitCode: 2
      };
    }
    if (options.autoCompress && options.file && options.create) {
      const file = options.file.toLowerCase();
      if (file.endsWith(".tar.gz") || file.endsWith(".tgz")) {
        options.gzip = true;
      } else if (file.endsWith(".tar.bz2") || file.endsWith(".tbz2")) {
        options.bzip2 = true;
      } else if (file.endsWith(".tar.xz") || file.endsWith(".txz")) {
        options.xz = true;
      } else if (file.endsWith(".tar.zst") || file.endsWith(".tzst")) {
        options.zstd = true;
      }
    }
    const compCount = [
      options.gzip,
      options.bzip2,
      options.xz,
      options.zstd
    ].filter(Boolean).length;
    if (compCount > 1) {
      return {
        stdout: "",
        stderr: "tar: You may not specify more than one compression option\n",
        exitCode: 2
      };
    }
    if ((options.append || options.update) && compCount > 0) {
      return {
        stdout: "",
        stderr: "tar: Cannot append/update compressed archives - decompress first\n",
        exitCode: 2
      };
    }
    let finalFiles = files;
    if (options.filesFrom) {
      const filesFromPath = ctx.fs.resolvePath(ctx.cwd, options.filesFrom);
      try {
        const content = await ctx.fs.readFile(filesFromPath);
        const additionalFiles = content.split("\n").map((line) => line.trim()).filter((line) => line.length > 0 && !line.startsWith("#"));
        finalFiles = [...files, ...additionalFiles];
      } catch {
        return {
          stdout: "",
          stderr: `tar: ${options.filesFrom}: Cannot open: No such file or directory
`,
          exitCode: 2
        };
      }
    }
    if (options.excludeFrom) {
      const excludeFromPath = ctx.fs.resolvePath(ctx.cwd, options.excludeFrom);
      try {
        const content = await ctx.fs.readFile(excludeFromPath);
        const additionalExcludes = content.split("\n").map((line) => line.trim()).filter((line) => line.length > 0 && !line.startsWith("#"));
        options.exclude.push(...additionalExcludes);
      } catch {
        return {
          stdout: "",
          stderr: `tar: ${options.excludeFrom}: Cannot open: No such file or directory
`,
          exitCode: 2
        };
      }
    }
    if (options.create) {
      return createTarArchive(ctx, options, finalFiles);
    } else if (options.append) {
      return appendTarArchive(ctx, options, finalFiles);
    } else if (options.update) {
      return updateTarArchive(ctx, options, finalFiles);
    } else if (options.extract) {
      return extractTarArchive(ctx, options, finalFiles);
    } else {
      return listTarArchive(ctx, options, finalFiles);
    }
  }
};
var flagsForFuzzing = {
  name: "tar",
  flags: [
    { flag: "-c", type: "boolean" },
    { flag: "-x", type: "boolean" },
    { flag: "-t", type: "boolean" },
    { flag: "-f", type: "value", valueHint: "path" },
    { flag: "-z", type: "boolean" },
    { flag: "-j", type: "boolean" },
    { flag: "-v", type: "boolean" },
    { flag: "-C", type: "value", valueHint: "path" },
    { flag: "--strip-components", type: "value", valueHint: "number" },
    { flag: "--exclude", type: "value", valueHint: "pattern" }
  ],
  needsArgs: true
};

export {
  tarCommand,
  flagsForFuzzing
};
