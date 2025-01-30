import { Block } from "./block";

export interface Chain {
    chain: Block[];
    length: number;
}