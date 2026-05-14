import "@testing-library/jest-native/extend-expect";

// Fail tests on console.error or console.warn
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.error = (message: string, ...args: any[]) => {
    originalConsoleError(message, ...args);
    throw new Error(`Test failed due to console.error: ${message}`);
};

console.warn = (message: string, ...args: any[]) => {
    originalConsoleWarn(message, ...args);
    throw new Error(`Test failed due to console.warn: ${message}`);
};
