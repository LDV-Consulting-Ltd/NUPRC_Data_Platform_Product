export default function Loading() {
  return (
    <div className="pc-state pc-state-loading" role="status">
      <h2>Loading</h2>
      <div className="pc-skel" />
      <div className="pc-skel" />
      <div className="pc-skel pc-skel-short" />
    </div>
  );
}
