// @ts-check

const ScrapMechanic = Module.findBaseAddress("ScrapMechanic.exe");
if (ScrapMechanic === null) {
    throw new Error("Module ScrapMechanic.exe not found. Make sure the game is running.");
}

const SerializeCharacter = ScrapMechanic.add(0x064fda0);
const NetObjUtil_SerializeNetId = ScrapMechanic.add(0x0654a70);
const Manager_FindById = ScrapMechanic.add(0x066a5c0);

let counter = 0;
const MAX_COUNTER = 2;

Interceptor.attach(SerializeCharacter, {
    onEnter(args) {
        counter = 0;

        if (!("rcx" in this.context)) {
            return; // For x64
        }
        // Clear the screen
        console.log("\x1b[2J\x1b[H");

        // On Windows x64, first four arguments are in rcx, rdx, r8, r9
        console.log("Function called at SerializeCharacter");
        console.log("Arg1 (rcx):", this.context.rcx);
        console.log("Arg2 (rdx):", this.context.rdx.and(0xff));
        console.log("Arg3 (r8):", this.context.r8);
        console.log("Arg4 (r9):", this.context.r9, this.context.r9.toInt32());

        console.log("Return address:", this.returnAddress.sub(0));
    },
    onLeave(retval) {
        console.log("Function returned:", retval);
        console.log();
    }
});

/**
 * ```c
 * struct BitStream
 * {
 *     uint32_t write_offset_bits;
 *     uint32_t read_offset_bits;
 *     char* write_buffer;
 *     uint32_t write_buffer_size_bits;
 *     char m_bOwnsData;
 *     __offset(0x108)
 *     char* read_buffer;
 * }
 * ```
 */
class BitStream {
    /**
     * @param {NativePointer} ptr 
     */
    constructor(ptr) {
        this.ptr = ptr;

        this.initial = this.snapshot();
    }

    get writeOffsetBits() {
        return this.ptr.add(0x0).readU32();
    }

    get readOffsetBits() {
        return this.ptr.add(0x4).readU32();
    }

    get writeBuffer() {
        return this.ptr.add(0x8).readPointer();
    }

    get writeBufferSizeBits() {
        return this.ptr.add(0x10).readU32();
    }

    get ownsData() {
        return this.ptr.add(0x14).readU8();
    }

    get readBuffer() {
        return this.ptr.add(0x108).readPointer();
    }

    snapshot() {
        return {
            writeOffsetBits: this.writeOffsetBits,
            readOffsetBits: this.readOffsetBits,
            writeBuffer: this.writeBuffer,
            writeBufferSizeBits: this.writeBufferSizeBits,
            ownsData: this.ownsData,
            readBuffer: this.readBuffer
        };
    }

    /**
     * @param {number} startBit
     * @param {number} bitCount
     * @returns {number[]}
     */
    viewBits(startBit, bitCount) {
        const bits = new Array(bitCount);
        const buffer = this.writeBuffer;

        const byteStart = Math.floor(startBit / 8);
        const byteCount = Math.ceil((startBit % 8 + bitCount) / 8);

        const byteArray = buffer.add(byteStart).readByteArray(byteCount);

        console.log(byteArray);

        if (byteArray === null) {
            throw new Error("Failed to read byte array from buffer.");
        }

        for (let i = startBit; i < startBit + bitCount; i++) {
            const byteIndex = Math.floor(i / 8) - byteStart;
            const bitIndex = i % 8;

            // console.log(`i: ${i}, Byte index: ${byteIndex}, Bit index: ${bitIndex}`);

            const byte = byteArray.unwrap().add(byteIndex).readU8();

            bits[i - startBit] = (byte >> (7 - bitIndex)) & 1;
        }

        const bin = bits.reduce((acc, bit, index) => {
            if (index % 8 === 0 && index !== 0) {
                acc += " ";
            }
            acc += bit;
            return acc;
        }, "");

        const hex = bin.split(" ").map(byte => parseInt(byte, 2).toString(16).padStart(2, "0")).join(" ");
        console.log(hex);


        return bits;
    }

    getWrittenSince(snapshot = this.initial) {
        const written = this.writeOffsetBits - snapshot.writeOffsetBits;
        return written > 0 ? written : 0;
    }
}

/**
 * @type {BitStream | null}
 */
let bitStream = null;

Interceptor.attach(NetObjUtil_SerializeNetId, {
    onEnter(args) {
        counter++;
        if (counter > MAX_COUNTER) {
            return; // Skip the second call to this function
        }

        if (!("rcx" in this.context)) {
            return; // For x64
        }

        // On Windows x64, first four arguments are in rcx, rdx, r8, r9
        console.log("Function called at NetObjUtil_SerializeNetId");
        console.log("Arg1 (rcx):", this.context.rcx);
        console.log("Arg2 (rdx):", this.context.rdx, this.context.rdx.toInt32());

        console.log("Return address:", this.returnAddress.sub(0));

        bitStream = new BitStream(this.context.rcx);
        console.log("Before:", JSON.stringify(bitStream.initial));
    },
    onLeave(retval) {
        if (counter > MAX_COUNTER) {
            return; // Skip the second call to this function
        }
        if (bitStream) {
            console.log("After:", JSON.stringify(bitStream.snapshot()));
            const written = bitStream.getWrittenSince();
            console.log("Written:", written);
            bitStream.viewBits(0, bitStream.initial.writeOffsetBits);
            // bitStream.viewBits(0, bitStream.writeOffsetBits);
            bitStream.viewBits(bitStream.initial.writeOffsetBits, written);
        }
        console.log("Function returned:", retval);
    }
});

// Interceptor.attach(Manager_FindById, {
//     onEnter(args) {
//         console.log("Manager_FindById");
//         for (let i = 0; i < 4; i++) {
//             console.log(` Arg${i + 1}:`, args[i]);
//         }

//         console.log(`  ${this.returnAddress}`);
//     },
//     onLeave(retval) {
//         console.log("Function returned:", retval);
//         // Clear the screen
//         console.log("\x1b[2J\x1b[H");
//     }
// });