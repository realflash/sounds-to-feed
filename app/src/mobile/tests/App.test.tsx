import React from "react";
import { render } from "@testing-library/react-native";
import { Text, View } from "react-native";

// Template Unit Test for Mobile
describe("Unit Test", () => {
  it("renders a basic component", () => {
    const { getByText } = render(
      <View>
        <Text>Hello World</Text>
      </View>
    );
    expect(getByText("Hello World")).toBeTruthy();
  });
});
