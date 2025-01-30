export interface Block {
    index: number;
    previous_hash: string;
    transactions: string | any[];
    timestamp: number;
    hash: string;
}